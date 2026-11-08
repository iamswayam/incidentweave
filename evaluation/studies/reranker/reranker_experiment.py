"""Development-only reranker export, execution, and deterministic analysis."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import tempfile
from collections.abc import Mapping, Sequence
from pathlib import Path
from statistics import mean
from typing import Any

from app.providers.reranker import RerankProvider, VoyageRerankFailure
from evaluation.manifest import MANIFEST_PATH, load_manifest, questions_for_split, sha256_file
from evaluation.metrics import (
    context_precision_at_k,
    first_relevant_span_rank,
    ndcg_at_k,
    recall_at_k,
    refusal_precision_recall,
)
from evaluation.scorecard import GUARD_THRESHOLD
from evaluation.stats import paired_comparison, stratified_bootstrap_interval
from evaluation.test_files import is_test_path

ROOT = Path(__file__).resolve().parents[3]
EXPERIMENT_DIR = Path("evaluation/experiments/reranker")
RANKINGS_PATH = EXPERIMENT_DIR / "development-rankings.json"
REPORT_JSON_PATH = EXPERIMENT_DIR / "development-report.json"
REPORT_MARKDOWN_PATH = EXPERIMENT_DIR / "report-development.md"
PIN_PATH = EXPERIMENT_DIR / "pin.json"
BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10_000
V1_REPOSITORIES = ("batch-processing-service", "incidentweave", "lifeos")
RETRIEVAL_METRICS = (
    "mrr_at_5",
    "hit_at_1",
    "hit_at_3",
    "hit_at_5",
    "hit_at_10",
    "hit_at_20",
    "ndcg_at_5",
    "ndcg_at_10",
    "recall_at_20",
    "context_precision_at_5",
    "test_file_share",
)
GUARD_GATES = {
    "guard.false_accept_rate": ("max_increase", 0.0),
    "guard.false_refusal_rate": ("max_increase", 0.02),
    "guard.correct_refusal_rate": ("max_decrease", 0.02),
}


def canonical_sha256(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def write_json_atomic(path: Path, value: Mapping[str, Any]) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = (
        json.dumps(
            value,
            indent=2,
            ensure_ascii=False,
            sort_keys=True,
            allow_nan=False,
        )
        + "\n"
    )
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def write_text_atomic(path: Path, content: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(content, encoding="utf-8", newline="\n")
    temporary.replace(path)


def require_development(split: str) -> None:
    if split != "development":
        raise ValueError("reranker experiment refuses any split other than development")


def validate_candidate_data(
    data: Mapping[str, Any],
    *,
    verify_source_split: bool = False,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> None:
    metadata = data.get("metadata")
    repositories = data.get("repositories")
    if not isinstance(metadata, Mapping):
        raise ValueError("candidate data has no metadata")
    require_development(str(metadata.get("split")))
    if metadata.get("repository_ids") != list(V1_REPOSITORIES):
        raise ValueError("candidate data does not contain the registered v1 repositories")
    if metadata.get("dataset_version") != "v1":
        raise ValueError("candidate data requires dataset_version 'v1'")
    if metadata.get("guard_threshold") != GUARD_THRESHOLD:
        raise ValueError("candidate data guard threshold differs from the scorecard")
    if not isinstance(repositories, list):
        raise ValueError("candidate data repositories must be a list")
    if any(not isinstance(row, Mapping) for row in repositories) or [
        row.get("id") for row in repositories
    ] != list(V1_REPOSITORIES):
        raise ValueError("candidate data repository rows do not match the registered v1 set")
    hashes = metadata.get("candidate_set_sha256")
    if not isinstance(hashes, Mapping):
        raise ValueError("candidate data has no candidate-set hashes")
    for repository in repositories:
        repo_id = str(repository["id"])
        questions = repository.get("questions")
        if not isinstance(questions, list):
            raise ValueError(f"{repo_id}: candidate questions must be a list")
        if any(not isinstance(question, Mapping) for question in questions):
            raise ValueError(f"{repo_id}: candidate question rows must be objects")
        question_ids = [question.get("id") for question in questions]
        if any(not isinstance(value, str) or not value for value in question_ids):
            raise ValueError(f"{repo_id}: candidate rows need question ids")
        if len(question_ids) != len(set(question_ids)):
            raise ValueError(f"{repo_id}: duplicate candidate question ids")
        for question in questions:
            candidates = question.get("baseline_candidates")
            if not isinstance(candidates, list) or len(candidates) > 20:
                raise ValueError(f"{repo_id}:{question['id']}: invalid top-20 candidate list")
            for candidate in candidates:
                if (
                    not isinstance(candidate, Mapping)
                    or not isinstance(candidate.get("chunk_id"), str)
                    or not isinstance(candidate.get("text"), str)
                    or not isinstance(candidate.get("file_path"), str)
                    or type(candidate.get("line_start")) is not int
                    or type(candidate.get("line_end")) is not int
                ):
                    raise ValueError(f"{repo_id}:{question['id']}: malformed candidate")
            distance = question.get("best_vector_distance")
            if distance is not None and (
                not isinstance(distance, (int, float))
                or isinstance(distance, bool)
                or not math.isfinite(distance)
            ):
                raise ValueError(f"{repo_id}:{question['id']}: invalid best vector distance")
            refused = question.get("guard_refused")
            if not isinstance(refused, bool) or refused != (
                distance is None or distance > GUARD_THRESHOLD
            ):
                raise ValueError(f"{repo_id}:{question['id']}: inconsistent guard decision")
            key = f"{repo_id}:{question['id']}"
            digest = canonical_sha256(candidates)
            if question.get("candidate_set_sha256") != digest or hashes.get(key) != digest:
                raise ValueError(f"{repo_id}:{question['id']}: candidate-set hash mismatch")
    if verify_source_split:
        from evaluation.golden import load_golden_set

        manifest = load_manifest(manifest_path, root=root)
        if manifest.get("schema_version") != 2:
            raise ValueError("reranker candidate data requires manifest schema version 2")
        if metadata.get("manifest_sha256") != sha256_file(manifest_path):
            raise ValueError("candidate manifest hash does not match the current manifest")
        entries = {entry["id"]: entry for entry in manifest["repositories"]}
        expected_dataset: dict[str, list[dict[str, Any]]] = {}
        for repository in repositories:
            repo_id = str(repository["id"])
            entry = entries[repo_id]
            fixture_hashes = metadata.get("fixture_sha256")
            if not isinstance(fixture_hashes, Mapping) or fixture_hashes.get(
                repo_id
            ) != sha256_file(root / entry["fixture"]["path"]):
                raise ValueError(f"{repo_id}: candidate fixture hash does not match the manifest")
            source = load_golden_set(root / entry["questions"]["path"])
            expected_questions = questions_for_split(entry, source["questions"], "development")
            expected_dataset[repo_id] = [
                {
                    "id": question["id"],
                    "category": question["category"],
                    "question": question["question"],
                    "relevant_spans": question["relevant_spans"],
                }
                for question in sorted(expected_questions, key=lambda row: row["id"])
            ]
            observed = {question["id"]: question for question in repository["questions"]}
            if set(observed) != {question["id"] for question in expected_dataset[repo_id]}:
                raise ValueError(f"{repo_id}: candidate rows are not exactly the development split")
            for expected in expected_dataset[repo_id]:
                actual = observed[expected["id"]]
                if any(actual.get(field) != expected[field] for field in expected if field != "id"):
                    raise ValueError(
                        f"{repo_id}:{expected['id']}: candidate labels differ from development data"
                    )
        if canonical_sha256(expected_dataset) != metadata.get("development_dataset_sha256"):
            raise ValueError("candidate development dataset hash does not match the source split")


def ensure_baseline_only(data: Mapping[str, Any]) -> None:
    if any(
        "rerank" in question
        for repository in data.get("repositories", [])
        for question in repository.get("questions", [])
    ):
        raise ValueError("candidate data already contains rerank results")


async def export_development_candidates(
    output_path: Path = RANKINGS_PATH,
    *,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    from evaluation.build_fixture import load_fixture
    from evaluation.golden import load_golden_set
    from evaluation.retrieval_eval import export_development_rankings
    from evaluation.scorecard import V1_REPOSITORIES as SCORECARD_REPOSITORIES
    from evaluation.scorecard import build_scorecard

    output_path = Path(output_path)
    if output_path.exists():
        existing = load_candidate_data(output_path)
        validate_candidate_data(
            existing,
            verify_source_split=True,
            manifest_path=manifest_path,
            root=root,
        )
        ensure_baseline_only(existing)
    if tuple(SCORECARD_REPOSITORIES) != V1_REPOSITORIES:
        raise ValueError("reranker candidate export requires the registered v1 repository set")
    manifest = load_manifest(manifest_path, root=root)
    if manifest.get("schema_version") != 2:
        raise ValueError("reranker candidate export requires manifest schema version 2")
    with tempfile.TemporaryDirectory(prefix="incidentweave-reranker-") as temp_dir:
        rankings = await export_development_rankings(
            Path(temp_dir) / "retrieval.json",
            manifest_path=manifest_path,
            root=root,
        )
    build_scorecard(rankings, manifest_path=manifest_path, root=root)
    if rankings["metadata"].get("split") != "development":
        raise ValueError("scorecard export is not development-only")
    entries = {entry["id"]: entry for entry in manifest["repositories"]}
    repositories = []
    fixture_hashes: dict[str, str] = {}
    development_dataset: dict[str, list[dict[str, Any]]] = {}
    candidate_hashes: dict[str, str] = {}
    for repo_id in V1_REPOSITORIES:
        entry = entries[repo_id]
        questions_data = load_golden_set(root / entry["questions"]["path"])
        questions = {
            row["id"]: row
            for row in questions_for_split(entry, questions_data["questions"], "development")
        }
        development_dataset[repo_id] = [
            {
                "id": question_id,
                "category": question["category"],
                "question": question["question"],
                "relevant_spans": question["relevant_spans"],
            }
            for question_id, question in sorted(questions.items())
        ]
        fixture_path = root / entry["fixture"]["path"]
        fixture_hashes[repo_id] = sha256_file(fixture_path)
        fixture = load_fixture(fixture_path)
        fixture_by_id = {
            f"{chunk['file_path']}:{chunk['line_start']}-{chunk['line_end']}": chunk
            for chunk in fixture["chunks"]
        }
        if len(fixture_by_id) != len(fixture["chunks"]):
            raise ValueError(f"{repo_id}: fixture contains duplicate candidate identifiers")
        export_repo = next(
            (row for row in rankings["repositories"] if row.get("id") == repo_id),
            None,
        )
        if export_repo is None:
            raise ValueError(f"{repo_id}: scorecard export is missing")
        exported_questions = []
        for row in export_repo["questions"]:
            question = questions.get(row["id"])
            if question is None:
                raise ValueError(f"{repo_id}:{row['id']}: question is not in development split")
            candidates = []
            for chunk in row["ranked_chunks_limit20"]:
                chunk_id = chunk["chunk_id"]
                fixture_chunk = fixture_by_id.get(chunk_id)
                if fixture_chunk is None:
                    raise ValueError(f"{repo_id}:{row['id']}: candidate is missing from fixture")
                text = fixture_chunk.get("content")
                if not isinstance(text, str) or not text:
                    raise ValueError(f"{repo_id}:{row['id']}: candidate text is missing")
                candidates.append(
                    {
                        "chunk_id": chunk_id,
                        "file_path": chunk["file_path"],
                        "line_start": chunk["line_start"],
                        "line_end": chunk["line_end"],
                        "text": text,
                    }
                )
            key = f"{repo_id}:{row['id']}"
            candidate_hashes[key] = canonical_sha256(candidates)
            exported_questions.append(
                {
                    "id": row["id"],
                    "question": question["question"],
                    "category": question["category"],
                    "relevant_spans": question["relevant_spans"],
                    "guard_refused": row["guard_refused"],
                    "best_vector_distance": row["best_vector_distance"],
                    "candidate_set_sha256": candidate_hashes[key],
                    "baseline_candidates": candidates,
                }
            )
        repositories.append({"id": repo_id, "questions": exported_questions})
    data = {
        "metadata": {
            "dataset_version": rankings["metadata"]["dataset_version"],
            "split": "development",
            "repository_ids": list(V1_REPOSITORIES),
            "retrieval_git_commit": rankings["metadata"]["git_commit"],
            "manifest_sha256": rankings["metadata"]["manifest_sha256"],
            "guard_threshold": GUARD_THRESHOLD,
            "development_dataset_sha256": canonical_sha256(development_dataset),
            "fixture_sha256": fixture_hashes,
            "retrieval_export_sha256": canonical_sha256(
                {key: value for key, value in rankings.items() if key != "exported_at"}
            ),
            "candidate_set_sha256": candidate_hashes,
        },
        "repositories": repositories,
    }
    validate_candidate_data(
        data,
        verify_source_split=True,
        manifest_path=manifest_path,
        root=root,
    )
    write_json_atomic(output_path, data)
    return data


def validate_candidate_set(
    baseline: Sequence[Mapping[str, Any]],
    treatment: Sequence[Mapping[str, Any]],
) -> None:
    baseline_by_id = {row.get("chunk_id"): row for row in baseline}
    treatment_by_id = {row.get("chunk_id"): row for row in treatment}
    if (
        len(baseline_by_id) != len(baseline)
        or len(treatment_by_id) != len(treatment)
        or set(baseline_by_id) != set(treatment_by_id)
        or any(
            baseline_by_id[key].get("text") != treatment_by_id[key].get("text")
            for key in baseline_by_id
        )
    ):
        raise AssertionError("reranker changed the candidate set or candidate text")


def apply_reranked_ids(
    candidates: Sequence[Mapping[str, Any]],
    ordered_ids: Sequence[str],
) -> list[dict[str, Any]]:
    by_id = {str(candidate["chunk_id"]): candidate for candidate in candidates}
    if len(by_id) != len(candidates) or len(ordered_ids) != len(candidates):
        raise AssertionError("reranker returned a different candidate set")
    if len(set(ordered_ids)) != len(ordered_ids) or set(ordered_ids) != set(by_id):
        raise AssertionError("reranker returned a different candidate set")
    treatment = [dict(by_id[chunk_id]) for chunk_id in ordered_ids]
    validate_candidate_set(candidates, treatment)
    return treatment


def load_pin(path: Path) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise ValueError(f"reranker pin is missing: {path}")
    try:
        pin = json.loads(path.read_text(encoding="utf-8-sig"))
    except json.JSONDecodeError as exc:
        raise ValueError("reranker pin must be valid JSON") from exc
    if not isinstance(pin, dict):
        raise ValueError("reranker pin must be a JSON object")
    _validate_pin(pin)
    return pin


def _validate_pin(pin: Mapping[str, Any]) -> None:
    forbidden = {"api_key", "voyage_api_key", "authorization", "secret", "token"}

    def reject_credentials(value: Any) -> None:
        if isinstance(value, Mapping):
            if any(str(key).casefold() in forbidden for key in value):
                raise ValueError("reranker pin must not contain credentials")
            for nested in value.values():
                reject_credentials(nested)
        elif isinstance(value, list):
            for nested in value:
                reject_credentials(nested)

    reject_credentials(pin)
    if not isinstance(pin.get("model_identifier"), str) or not pin["model_identifier"].strip():
        raise ValueError("pin must include model_identifier")
    if pin.get("api_version") != "v1":
        raise ValueError("pin api_version must be 'v1'")
    if pin.get("model_settings") != {}:
        raise ValueError("pin model_settings must be an empty object for the registered API")
    limits = pin.get("request_limits")
    if not isinstance(limits, Mapping):
        raise ValueError("pin must include request_limits")
    if (
        type(limits.get("max_candidates")) is not int
        or limits["max_candidates"] != 20
        or type(limits.get("top_k")) is not int
        or limits["top_k"] != 20
    ):
        raise ValueError("pin must set max_candidates and top_k to 20")
    if type(limits.get("truncation")) is not bool:
        raise ValueError("pin truncation must be a boolean")
    timeout = limits.get("timeout_seconds")
    attempts = limits.get("max_attempts")
    if (
        not isinstance(timeout, (int, float))
        or isinstance(timeout, bool)
        or not math.isfinite(timeout)
        or timeout <= 0
    ):
        raise ValueError("pin timeout_seconds must be positive")
    if type(attempts) is not int or not 1 <= attempts <= 5:
        raise ValueError("pin max_attempts must be between 1 and 5")
    retry_policy = pin.get("retry_policy")
    if not isinstance(retry_policy, Mapping):
        raise ValueError("pin must include retry_policy")
    initial_delay = retry_policy.get("initial_delay_seconds")
    max_delay = retry_policy.get("max_delay_seconds")
    if (
        retry_policy.get("strategy") != "exponential"
        or type(retry_policy.get("respect_retry_after")) is not bool
        or not isinstance(initial_delay, (int, float))
        or isinstance(initial_delay, bool)
        or not math.isfinite(initial_delay)
        or initial_delay <= 0
        or not isinstance(max_delay, (int, float))
        or isinstance(max_delay, bool)
        or not math.isfinite(max_delay)
        or max_delay < initial_delay
    ):
        raise ValueError("pin retry_policy is invalid")
    pricing = pin.get("pricing")
    if not isinstance(pricing, Mapping):
        raise ValueError("pin must include pricing and its source")
    price = pricing.get("usd_per_million_tokens")
    if (
        not isinstance(price, (int, float))
        or isinstance(price, bool)
        or not math.isfinite(price)
        or price < 0
    ):
        raise ValueError("pin pricing must include a non-negative USD per million tokens")
    if not isinstance(pricing.get("source_url"), str) or not pricing["source_url"].strip():
        raise ValueError("pin pricing must include source_url")


async def rerank_candidates(
    data: Mapping[str, Any],
    pin: Mapping[str, Any],
    provider: RerankProvider,
    *,
    verify_source_split: bool = False,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    _validate_pin(pin)
    metadata = data.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("candidate data has no metadata")
    validate_candidate_data(
        data,
        verify_source_split=verify_source_split,
        manifest_path=manifest_path,
        root=root,
    )
    ensure_baseline_only(data)
    result = json.loads(json.dumps(data))
    result_metadata = result["metadata"]
    result_metadata["reranker_pin"] = dict(pin)
    failures = 0
    for repository in result.get("repositories", []):
        for question in repository.get("questions", []):
            baseline = question.get("baseline_candidates")
            if not isinstance(baseline, list):
                raise ValueError("candidate row has no baseline_candidates")
            if not baseline:
                failures += 1
                question["treatment_candidates"] = []
                question["rerank"] = {
                    "response": None,
                    "attempts": [],
                    "latency_ms": 0,
                    "attempt_count": 0,
                    "token_count": None,
                    "estimated_cost_usd": None,
                    "fallback_used": True,
                    "error": {"error_class": "no_candidates", "status_code": None},
                }
                continue
            documents = [candidate["text"] for candidate in baseline]
            started = asyncio.get_running_loop().time()
            try:
                response = await provider.rerank(
                    question["question"],
                    documents,
                    top_k=min(pin["request_limits"]["top_k"], len(documents)),
                    truncation=pin["request_limits"]["truncation"],
                    timeout_seconds=float(pin["request_limits"]["timeout_seconds"]),
                    max_attempts=pin["request_limits"]["max_attempts"],
                    retry_policy=pin["retry_policy"],
                )
                if any(
                    type(index) is not int or not 0 <= index < len(baseline)
                    for index in response.indices
                ):
                    raise AssertionError("reranker returned a different candidate set")
                ordered_ids = [baseline[index]["chunk_id"] for index in response.indices]
                treatment = apply_reranked_ids(baseline, ordered_ids)
                question["treatment_candidates"] = treatment
                question["rerank"] = {
                    "response": dict(response.response),
                    "attempts": [dict(row) for row in response.attempt_records],
                    "latency_ms": response.latency_ms,
                    "attempt_count": response.attempt_count,
                    "token_count": response.token_count,
                    "estimated_cost_usd": (
                        response.token_count * pin["pricing"]["usd_per_million_tokens"] / 1_000_000
                        if response.token_count is not None
                        else None
                    ),
                    "fallback_used": False,
                    "error": None,
                }
            except (VoyageRerankFailure, TimeoutError) as exc:
                failures += 1
                error_class = exc.error_class if isinstance(exc, VoyageRerankFailure) else "timeout"
                latency_ms = (
                    exc.latency_ms
                    if isinstance(exc, VoyageRerankFailure)
                    else round((asyncio.get_running_loop().time() - started) * 1000)
                )
                question["treatment_candidates"] = [dict(candidate) for candidate in baseline]
                question["rerank"] = {
                    "response": None,
                    "attempts": [dict(row) for row in getattr(exc, "attempt_records", ())],
                    "latency_ms": latency_ms,
                    "attempt_count": exc.attempts if isinstance(exc, VoyageRerankFailure) else 0,
                    "token_count": None,
                    "estimated_cost_usd": None,
                    "fallback_used": True,
                    "error": {
                        "error_class": error_class,
                        "status_code": (
                            exc.status_code if isinstance(exc, VoyageRerankFailure) else None
                        ),
                    },
                }
    result_metadata["rerank_failure_count"] = failures
    return result


def _metric_values(
    candidates: Sequence[Mapping[str, Any]],
    spans: Sequence[Mapping[str, Any]],
    corpus: Sequence[Mapping[str, Any]],
) -> dict[str, float]:
    if not spans:
        return {}
    rank = first_relevant_span_rank(candidates[:5], spans)
    values = {
        "mrr_at_5": 1 / rank if rank is not None else 0.0,
        "ndcg_at_5": ndcg_at_k(candidates, spans, corpus, 5),
        "ndcg_at_10": ndcg_at_k(candidates, spans, corpus, 10),
        "recall_at_20": recall_at_k(candidates, spans, 20),
        "context_precision_at_5": context_precision_at_k(candidates, spans, 5),
    }
    for k in (1, 3, 5, 10, 20):
        values[f"hit_at_{k}"] = float(first_relevant_span_rank(candidates[:k], spans) is not None)
    top_five = candidates[:5]
    values["test_file_share"] = (
        sum(is_test_path(str(chunk["file_path"])) for chunk in top_five) / len(top_five)
        if top_five
        else 0.0
    )
    return values


def _nearest_rank(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    return ordered[max(0, math.ceil(percentile * len(ordered)) - 1)]


def _mean(values: Sequence[float]) -> float | None:
    return mean(values) if values else None


def _rates(questions: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    answerable = [q for q in questions if not str(q["category"]).startswith("unanswerable")]
    unanswerable = [q for q in questions if str(q["category"]).startswith("unanswerable")]
    refused = [bool(q["guard_refused"]) for q in questions]
    labels = [not str(q["category"]).startswith("unanswerable") for q in questions]
    refusal = refusal_precision_recall(labels, refused)
    tp, fp, fn = (
        int(refusal["true_positive"]),
        int(refusal["false_positive"]),
        int(refusal["false_negative"]),
    )
    return {
        "guard.false_accept_rate": (
            sum(not bool(q["guard_refused"]) for q in unanswerable) / len(unanswerable)
            if unanswerable
            else None
        ),
        "guard.correct_refusal_rate": (
            sum(bool(q["guard_refused"]) for q in unanswerable) / len(unanswerable)
            if unanswerable
            else None
        ),
        "guard.false_refusal_rate": (
            sum(bool(q["guard_refused"]) for q in answerable) / len(answerable)
            if answerable
            else None
        ),
        "guard.refusal_precision": tp / (tp + fp) if tp + fp else None,
        "guard.refusal_recall": tp / (tp + fn) if tp + fn else None,
    }


def _guard_sample_counts(questions: Sequence[Mapping[str, Any]]) -> dict[str, int]:
    answerable_n = sum(
        not str(question["category"]).startswith("unanswerable") for question in questions
    )
    unanswerable_n = len(questions) - answerable_n
    refused_n = sum(bool(question["guard_refused"]) for question in questions)
    return {
        "n": len(questions),
        "guard.false_accept_rate": unanswerable_n,
        "guard.correct_refusal_rate": unanswerable_n,
        "guard.false_refusal_rate": answerable_n,
        "guard.refusal_precision": refused_n,
        "guard.refusal_recall": unanswerable_n,
    }


def _metric_summary(
    rows: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for metric in RETRIEVAL_METRICS:
        values = [row for row in rows if row["baseline"].get(metric) is not None]
        if not values:
            output[metric] = {
                "n": 0,
                "baseline": None,
                "treatment": None,
                "treatment_minus_baseline": None,
                "bootstrap_95": None,
            }
            continue
        differences = [float(row["differences"][metric]) for row in values]
        strata: dict[str, list[float]] = {}
        for row in values:
            strata.setdefault(str(row["repository_id"]), []).append(
                float(row["differences"][metric])
            )
        interval = stratified_bootstrap_interval(
            strata,
            lambda sample: sum(sample) / len(sample),
            seed=BOOTSTRAP_SEED,
            resamples=BOOTSTRAP_RESAMPLES,
        )
        summary = {
            "n": len(values),
            "baseline": _mean([float(row["baseline"][metric]) for row in values]),
            "treatment": _mean([float(row["treatment"][metric]) for row in values]),
            "treatment_minus_baseline": _mean(differences),
            "bootstrap_95": list(interval),
        }
        if metric.startswith("hit_at_"):
            comparison = paired_comparison(
                [bool(row["baseline"][metric]) for row in values],
                [bool(row["treatment"][metric]) for row in values],
            )
            summary["paired_comparison"] = comparison
        output[metric] = summary
    return output


def decide_reranker(
    *,
    mrr: Mapping[str, Any],
    guard_baseline: Mapping[str, float | None],
    guard_treatment: Mapping[str, float | None],
    latency: Mapping[str, Any],
    cost: Mapping[str, Any],
) -> dict[str, Any]:
    failures: list[str] = []
    improvement = mrr.get("treatment_minus_baseline")
    interval = mrr.get("bootstrap_95")
    if (
        not isinstance(improvement, (int, float))
        or isinstance(improvement, bool)
        or not math.isfinite(improvement)
        or improvement < 0.02
    ):
        failures.append("MRR@5 improvement is below 0.02 absolute")
    if (
        not isinstance(interval, (list, tuple))
        or len(interval) != 2
        or any(
            not isinstance(bound, (int, float))
            or isinstance(bound, bool)
            or not math.isfinite(bound)
            for bound in interval
        )
        or interval[0] <= 0
    ):
        failures.append("MRR@5 paired 95% interval lower bound is not above zero")
    for name, (direction, margin) in GUARD_GATES.items():
        before, after = guard_baseline.get(name), guard_treatment.get(name)
        if (
            not isinstance(before, (int, float))
            or isinstance(before, bool)
            or not math.isfinite(before)
            or not isinstance(after, (int, float))
            or isinstance(after, bool)
            or not math.isfinite(after)
        ):
            failures.append(f"{name} is unavailable")
        elif direction == "max_increase" and after > before + margin:
            failures.append(f"{name} worsened beyond {margin:.2f} absolute")
        elif direction == "max_decrease" and after < before - margin:
            failures.append(f"{name} worsened beyond {margin:.2f} absolute")
    p50, p95 = latency.get("p50_ms"), latency.get("p95_ms")
    if (
        not isinstance(p50, (int, float))
        or isinstance(p50, bool)
        or not math.isfinite(p50)
        or p50 > 500
    ):
        failures.append("added median latency exceeds 500 ms or is unavailable")
    if (
        not isinstance(p95, (int, float))
        or isinstance(p95, bool)
        or not math.isfinite(p95)
        or p95 > 1500
    ):
        failures.append("added p95 latency exceeds 1,500 ms or is unavailable")
    cost_value = cost.get("cost_per_1000_queries_usd")
    if (
        not isinstance(cost_value, (int, float))
        or isinstance(cost_value, bool)
        or not math.isfinite(cost_value)
        or cost_value < 0
    ):
        failures.append("cost per 1,000 queries is unavailable")
    return {"decision": "REJECT" if failures else "KEEP", "failing_conditions": failures}


def analyze_experiment(
    data: Mapping[str, Any],
    fixture_chunks_by_repo: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    verify_source_split: bool = False,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    metadata = data.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("experiment data has no metadata")
    validate_candidate_data(
        data,
        verify_source_split=verify_source_split,
        manifest_path=manifest_path,
        root=root,
    )
    repositories = data.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ValueError("experiment data has no repositories")
    pin = metadata.get("reranker_pin")
    if not isinstance(pin, Mapping):
        raise ValueError("experiment data has no pinned reranker settings")
    _validate_pin(pin)
    price = float(pin["pricing"]["usd_per_million_tokens"])
    question_rows: list[dict[str, Any]] = []
    guard_by_repo: dict[str, list[Mapping[str, Any]]] = {}
    latencies: list[float] = []
    token_counts: list[int] = []
    estimated_costs: list[float] = []
    for repository in repositories:
        repo_id = str(repository.get("id"))
        corpus = fixture_chunks_by_repo.get(repo_id)
        questions = repository.get("questions")
        if corpus is None or not isinstance(questions, list):
            raise ValueError(f"{repo_id}: missing corpus or question rows")
        guard_by_repo[repo_id] = questions
        for question in questions:
            rerank = question.get("rerank")
            if not isinstance(rerank, Mapping):
                raise ValueError(f"{repo_id}:{question.get('id')}: treatment is missing")
            latency_ms = rerank.get("latency_ms")
            if (
                not isinstance(latency_ms, (int, float))
                or isinstance(latency_ms, bool)
                or not math.isfinite(latency_ms)
                or latency_ms < 0
            ):
                raise ValueError(f"{repo_id}:{question.get('id')}: invalid rerank latency")
            if not isinstance(rerank.get("attempts"), list):
                raise ValueError(f"{repo_id}:{question.get('id')}: rerank attempts are missing")
            if type(rerank.get("fallback_used")) is not bool:
                raise ValueError(f"{repo_id}:{question.get('id')}: invalid fallback marker")
            token_count = rerank.get("token_count")
            if token_count is not None and (type(token_count) is not int or token_count < 0):
                raise ValueError(f"{repo_id}:{question.get('id')}: invalid token count")
            estimated_cost = token_count * price / 1_000_000 if token_count is not None else None
            if rerank.get("estimated_cost_usd") != estimated_cost:
                raise ValueError(
                    f"{repo_id}:{question.get('id')}: invalid estimated operation cost"
                )
            baseline = question.get("baseline_candidates")
            treatment = question.get("treatment_candidates")
            validate_candidate_set(baseline, treatment)
            before = _metric_values(baseline, question["relevant_spans"], corpus)
            after = _metric_values(treatment, question["relevant_spans"], corpus)
            differences = {
                metric: after[metric] - before[metric] for metric in before.keys() & after.keys()
            }
            question_rows.append(
                {
                    "repository_id": repo_id,
                    "question_id": question["id"],
                    "baseline": before,
                    "treatment": after,
                    "differences": differences,
                    "latency_ms": float(latency_ms),
                    "token_count": token_count,
                    "estimated_cost_usd": estimated_cost,
                    "fallback_used": rerank["fallback_used"],
                    "error": rerank.get("error"),
                }
            )
            latencies.append(float(latency_ms))
            if token_count is not None:
                token_counts.append(token_count)
                estimated_costs.append(float(estimated_cost))
    pooled_rows = question_rows
    pooled = _metric_summary(pooled_rows)
    by_repository = {
        str(repository["id"]): _metric_summary(
            [row for row in question_rows if row["repository_id"] == str(repository["id"])]
        )
        for repository in repositories
    }
    guard_baseline = _rates([q for rows in guard_by_repo.values() for q in rows])
    guard_treatment = _rates([q for rows in guard_by_repo.values() for q in rows])
    guard_by_repository = {
        repo_id: {"baseline": _rates(rows), "treatment": _rates(rows)}
        for repo_id, rows in guard_by_repo.items()
    }
    guard_counts_by_repository = {
        repo_id: _guard_sample_counts(rows) for repo_id, rows in guard_by_repo.items()
    }
    guard_sample_counts = _guard_sample_counts(
        [question for rows in guard_by_repo.values() for question in rows]
    )
    query_count = len(question_rows)
    missing_token_count = query_count - len(token_counts)
    cost_value = (
        sum(estimated_costs) * 1000 / query_count
        if query_count and len(estimated_costs) == query_count
        else None
    )
    latency_summary = {
        "query_count": query_count,
        "recorded_queries": len(latencies),
        "p50_ms": _nearest_rank(latencies, 0.5),
        "p95_ms": _nearest_rank(latencies, 0.95),
        "percentile_method": "nearest-rank",
    }
    cost_summary = {
        "cost_per_1000_queries_usd": cost_value,
        "token_count_sum": sum(token_counts),
        "token_counted_queries": len(token_counts),
        "missing_token_count_queries": missing_token_count,
        "usd_per_million_tokens": price,
        "pricing_source_url": pin["pricing"]["source_url"],
    }
    decision = decide_reranker(
        mrr=pooled["mrr_at_5"],
        guard_baseline=guard_baseline,
        guard_treatment=guard_treatment,
        latency=latency_summary,
        cost=cost_summary,
    )
    errors = sum(
        bool(q["rerank"].get("fallback_used")) for rows in guard_by_repo.values() for q in rows
    )
    if metadata.get("rerank_failure_count") not in {None, errors}:
        raise ValueError("rerank failure count does not match recorded question outcomes")
    return {
        "metadata": {
            **dict(metadata),
            "bootstrap_seed": BOOTSTRAP_SEED,
            "bootstrap_resamples": BOOTSTRAP_RESAMPLES,
            "bootstrap_confidence": 0.95,
        },
        "question_count": query_count,
        "per_question": question_rows,
        "per_repository": by_repository,
        "guard_metrics_per_repository": guard_by_repository,
        "guard_sample_counts": {
            "pooled": guard_sample_counts,
            "per_repository": guard_counts_by_repository,
        },
        "pooled": pooled,
        "guard_metrics": {"baseline": guard_baseline, "treatment": guard_treatment},
        "latency": latency_summary,
        "cost": cost_summary,
        "rerank_failure_count": errors,
        "decision": decision,
    }


def format_report(report: Mapping[str, Any]) -> str:
    decision = report["decision"]
    lines = [
        "# Reranker development report",
        "",
        f"Decision: **{decision['decision']}**",
        "",
        "## Primary metric",
        "",
        (
            "Paired, repository-stratified 95% percentile bootstrap interval "
            f"(seed {BOOTSTRAP_SEED}; {BOOTSTRAP_RESAMPLES:,} resamples; "
            "linear interpolation)."
        ),
        "",
        "| Scope | n | Baseline MRR@5 | Treatment MRR@5 | Difference | Paired 95% interval |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for scope, metrics in [
        *[(repo, value) for repo, value in report["per_repository"].items()],
        ("Pooled", report["pooled"]),
    ]:
        metric = metrics["mrr_at_5"]
        interval = metric["bootstrap_95"]
        interval_text = (
            "unavailable" if interval is None else f"[{interval[0]:.4f}, {interval[1]:.4f}]"
        )
        lines.append(
            f"| {scope} | {metric['n']} | {metric['baseline']} | {metric['treatment']} | "
            f"{metric['treatment_minus_baseline']} | {interval_text} |"
        )
    lines.extend(["", "## Decision conditions", ""])
    if decision["failing_conditions"]:
        lines.extend(f"- FAIL: {condition}" for condition in decision["failing_conditions"])
    else:
        lines.append("- All registered decision gates passed.")
    lines.extend(
        [
            "",
            "## Secondary retrieval metrics",
            "",
            "| Metric | Baseline | Treatment | Difference | n | Wins | Losses | Ties | "
            "Sign-test p |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for name, metric in report["pooled"].items():
        if name == "mrr_at_5":
            continue
        comparison = metric.get("paired_comparison", {})
        lines.append(
            f"| {name} | {metric['baseline']} | {metric['treatment']} | "
            f"{metric['treatment_minus_baseline']} | {metric['n']} | "
            f"{comparison.get('wins', '-')} | {comparison.get('losses', '-')} | "
            f"{comparison.get('ties', '-')} | {comparison.get('p_value', '-')} |"
        )
    lines.extend(
        [
            "",
            "## Guard metrics",
            "",
            "| Scope | Metric | n | Baseline | Treatment |",
            "|---|---|---:|---:|---:|",
        ]
    )
    guard_scopes = [
        *[(repo_id, values) for repo_id, values in report["guard_metrics_per_repository"].items()],
        ("Pooled", report["guard_metrics"]),
    ]
    for scope, values in guard_scopes:
        counts = (
            report["guard_sample_counts"]["per_repository"][scope]
            if scope != "Pooled"
            else report["guard_sample_counts"]["pooled"]
        )
        for metric in (
            "guard.false_accept_rate",
            "guard.correct_refusal_rate",
            "guard.false_refusal_rate",
            "guard.refusal_precision",
            "guard.refusal_recall",
        ):
            baseline_value = values["baseline"][metric]
            lines.append(
                f"| {scope} | {metric} | {counts[metric]} | {baseline_value} | "
                f"{values['treatment'][metric]} |"
            )
    lines.extend(
        [
            "",
            "## Latency, cost, and errors",
            "",
            f"- Added latency: p50={report['latency']['p50_ms']} ms; "
            f"p95={report['latency']['p95_ms']} ms (nearest-rank).",
            f"- Cost per 1,000 queries: {report['cost']['cost_per_1000_queries_usd']} USD.",
            f"- Estimated list-price cost per operation: "
            f"{report['cost']['usd_per_million_tokens']} USD per million tokens "
            f"({report['cost']['pricing_source_url']}).",
            f"- Rerank failures with baseline fallback: {report['rerank_failure_count']}.",
            "",
            "## Per-question paired differences",
            "",
            "| Repository | Question | Added latency (ms) | Tokens | Estimated cost (USD) | "
            "Fallback | Metric differences |",
            "|---|---|---:|---:|---:|---|---|",
        ]
    )
    for row in report["per_question"]:
        lines.append(
            f"| {row['repository_id']} | {row['question_id']} | {row['latency_ms']} | "
            f"{row['token_count']} | {row['estimated_cost_usd']} | "
            f"{row['fallback_used']} | "
            f"`{json.dumps(row['differences'], sort_keys=True)}` |"
        )
    return "\n".join(lines) + "\n"


def load_candidate_data(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"cannot load reranker candidate data: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError("reranker candidate data must be a JSON object")
    return data


async def run_rerank_stage(
    input_path: Path,
    *,
    pin_path: Path = PIN_PATH,
    output_path: Path | None = None,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    import httpx

    from app.providers.reranker import VoyageRerankAdapter
    from app.providers.usage import DbUsageLogger

    data = load_candidate_data(input_path)
    validate_candidate_data(
        data,
        verify_source_split=True,
        manifest_path=manifest_path,
        root=root,
    )
    ensure_baseline_only(data)
    pin = load_pin(pin_path)
    api_key = get_voyage_api_key(root)
    async with httpx.AsyncClient() as client:
        provider = VoyageRerankAdapter(
            api_key=api_key,
            model=pin["model_identifier"],
            api_version=pin["api_version"],
            client=client,
            usage_logger=DbUsageLogger(),
        )
        result = await rerank_candidates(
            data,
            pin,
            provider,
            verify_source_split=False,
            manifest_path=manifest_path,
            root=root,
        )
    write_json_atomic(Path(output_path or input_path), result)
    return result


def run_analysis_stage(
    input_path: Path,
    *,
    json_output: Path = REPORT_JSON_PATH,
    markdown_output: Path = REPORT_MARKDOWN_PATH,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    from evaluation.build_fixture import load_fixture

    data = load_candidate_data(input_path)
    validate_candidate_data(
        data,
        verify_source_split=True,
        manifest_path=manifest_path,
        root=root,
    )
    manifest = load_manifest(manifest_path, root=root)
    entries = {entry["id"]: entry for entry in manifest["repositories"]}
    fixture_chunks_by_repo = {
        repo_id: load_fixture(root / entries[repo_id]["fixture"]["path"])["chunks"]
        for repo_id in V1_REPOSITORIES
    }
    report = analyze_experiment(
        data,
        fixture_chunks_by_repo,
        verify_source_split=False,
        manifest_path=manifest_path,
        root=root,
    )
    write_json_atomic(json_output, report)
    write_text_atomic(markdown_output, format_report(report))
    return report


def get_voyage_api_key(repo_root: Path) -> str:
    from dotenv import dotenv_values

    key = dotenv_values(Path(repo_root) / ".env").get("VOYAGE_API_KEY")
    if not isinstance(key, str) or not key:
        raise ValueError("VOYAGE_API_KEY is missing from the local .env")
    return key
