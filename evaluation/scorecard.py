"""Pure scoring helpers for the registered retrieval and guard scorecard."""

from __future__ import annotations

import json
import math
import subprocess
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from evaluation.build_fixture import load_fixture
from evaluation.golden import load_golden_set
from evaluation.manifest import (
    MANIFEST_PATH,
    load_manifest,
    questions_for_split,
    sha256_file,
)
from evaluation.metrics import (
    auroc,
    context_precision_at_k,
    first_relevant_span_rank,
    guard_confusion,
    ndcg_at_k,
    recall_at_k,
    refusal_precision_recall,
    span_hit_at_k,
)
from evaluation.stats import stratified_bootstrap_interval, wilson_interval

ROOT = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = "docs/architecture-review/16-scorecard-protocol.md"
V1_REPOSITORIES = ("batch-processing-service", "incidentweave", "lifeos")
BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10_000
GUARD_THRESHOLD = 0.5


def _validate_export(
    export: Mapping[str, Any],
    manifest: Mapping[str, Any],
    manifest_path: Path,
    root: Path,
) -> dict[str, list[dict[str, Any]]]:
    metadata = export.get("metadata")
    if not isinstance(metadata, Mapping):
        raise ValueError("Rankings export metadata must be an object")
    if metadata.get("split") != "development":
        raise ValueError("Scorecard refuses any split other than development")
    if metadata.get("dataset_version") != "v1":
        raise ValueError("V1 scorecard requires dataset_version 'v1'")
    if metadata.get("repository_ids") != list(V1_REPOSITORIES):
        raise ValueError("Rankings export must contain exactly the v1 repositories")
    if not isinstance(metadata.get("git_commit"), str) or not metadata["git_commit"]:
        raise ValueError("Rankings export must record the retrieval code commit")
    if metadata.get("manifest_sha256") != sha256_file(manifest_path):
        raise ValueError("Rankings export manifest hash does not match the current manifest")

    entries = {entry["id"]: entry for entry in manifest["repositories"]}
    if tuple(sorted(entries)) != V1_REPOSITORIES:
        raise ValueError("V1 scorecard requires exactly the three v1 manifest repositories")
    raw_repositories = export.get("repositories")
    if not isinstance(raw_repositories, list):
        raise ValueError("Rankings export repositories must be a list")
    exported = {
        row.get("id"): row
        for row in raw_repositories
        if isinstance(row, Mapping)
    }
    if set(exported) != set(V1_REPOSITORIES) or len(exported) != len(raw_repositories):
        raise ValueError("Rankings export repository rows do not match the v1 repositories")

    selected_by_repo: dict[str, list[dict[str, Any]]] = {}
    for repo_id in V1_REPOSITORIES:
        entry = entries[repo_id]
        question_data = load_golden_set(root / entry["questions"]["path"])
        expected = questions_for_split(entry, question_data["questions"], "development")
        expected_by_id = {question["id"]: question for question in expected}
        rows = exported[repo_id].get("questions")
        if not isinstance(rows, list):
            raise ValueError(f"{repo_id}: exported questions must be a list")
        by_id = {
            row.get("id"): row
            for row in rows
            if isinstance(row, Mapping) and isinstance(row.get("id"), str)
        }
        if len(by_id) != len(rows) or set(by_id) != set(expected_by_id):
            raise ValueError(
                f"{repo_id}: export must contain exactly the development questions"
            )
        selected = []
        for question_id, question in expected_by_id.items():
            row = by_id[question_id]
            if row.get("repository") != repo_id or row.get("category") != question["category"]:
                raise ValueError(f"{repo_id}:{question_id}: exported labels do not match")
            ranked = row.get("ranked_chunks")
            if not isinstance(ranked, list) or len(ranked) > 20:
                raise ValueError(f"{repo_id}:{question_id}: invalid top-20 ranked chunks")
            for chunk in ranked:
                if (
                    not isinstance(chunk, Mapping)
                    or not isinstance(chunk.get("chunk_id"), str)
                    or not isinstance(chunk.get("file_path"), str)
                    or not isinstance(chunk.get("line_start"), int)
                    or not isinstance(chunk.get("line_end"), int)
                    or (
                        chunk.get("vector_distance") is not None
                        and not isinstance(chunk.get("vector_distance"), (int, float))
                    )
                ):
                    raise ValueError(f"{repo_id}:{question_id}: malformed ranked chunk")
            best_distance = row.get("best_vector_distance")
            if best_distance is not None and not isinstance(best_distance, (int, float)):
                raise ValueError(f"{repo_id}:{question_id}: invalid best vector distance")
            observed_distances = [
                float(chunk["vector_distance"])
                for chunk in ranked[:5]
                if chunk["vector_distance"] is not None
            ]
            observed_best = min(observed_distances) if observed_distances else None
            if (
                (best_distance is None) != (observed_best is None)
                or (
                    best_distance is not None
                    and observed_best is not None
                    and not math.isclose(float(best_distance), observed_best)
                )
            ):
                raise ValueError(f"{repo_id}:{question_id}: best vector distance is inconsistent")
            refused = row.get("guard_refused")
            if not isinstance(refused, bool):
                raise ValueError(f"{repo_id}:{question_id}: missing guard decision")
            expected_refusal = best_distance is None or best_distance > GUARD_THRESHOLD
            if refused != expected_refusal:
                raise ValueError(f"{repo_id}:{question_id}: guard decision is inconsistent")
            selected.append({**row, **question})
        selected_by_repo[repo_id] = selected
    return selected_by_repo


def _wilson(successes: int, n: int) -> dict[str, Any]:
    low, high = wilson_interval(successes, n)
    return {
        "value": successes / n if n else None,
        "successes": successes,
        "n": n,
        "wilson_95": [low, high],
    }


def _bootstrap_mean(
    rows_by_repo: Mapping[str, Sequence[dict[str, Any]]],
    field: str,
    repo_ids: Sequence[str],
) -> dict[str, Any]:
    rows = [row for repo_id in repo_ids for row in rows_by_repo[repo_id]]
    if not rows:
        return {"value": None, "n": 0, "bootstrap_95": None}
    value = sum(float(row[field]) for row in rows) / len(rows)
    interval = stratified_bootstrap_interval(
        {repo: rows_by_repo[repo] for repo in repo_ids},
        lambda sample: sum(float(row[field]) for row in sample) / len(sample),
        seed=BOOTSTRAP_SEED,
        resamples=BOOTSTRAP_RESAMPLES,
    )
    return {"value": value, "n": len(rows), "bootstrap_95": list(interval)}


def _auroc_metric(
    rows_by_repo: Mapping[str, Sequence[dict[str, Any]]],
    repo_ids: Sequence[str],
) -> dict[str, Any]:
    rows = [row for repo_id in repo_ids for row in rows_by_repo[repo_id]]
    if any(row["best_vector_distance"] is None for row in rows):
        return {
            "value": None,
            "n": len(rows),
            "bootstrap_95": None,
            "reason": "one or more questions have no vector distance",
        }
    def positive(row: dict[str, Any]) -> bool:
        return str(row["category"]).startswith("unanswerable")

    value = auroc(
        [float(row["best_vector_distance"]) for row in rows],
        [positive(row) for row in rows],
    )
    strata: dict[str, list[dict[str, Any]]] = {}
    for repo_id in repo_ids:
        for row in rows_by_repo[repo_id]:
            key = f"{repo_id}:{positive(row)}"
            strata.setdefault(key, []).append(row)
    interval = stratified_bootstrap_interval(
        strata,
        lambda sample: auroc(
            [float(row["best_vector_distance"]) for row in sample],
            [positive(row) for row in sample],
        ),
        seed=BOOTSTRAP_SEED,
        resamples=BOOTSTRAP_RESAMPLES,
    )
    return {"value": value, "n": len(rows), "bootstrap_95": list(interval)}


def _threshold_sweep(rows: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    answerable = [
        row for row in rows if not str(row["category"]).startswith("unanswerable")
    ]
    unanswerable = [row for row in rows if row not in answerable]
    output = []
    for index in range(17):
        threshold = round(0.3 + index * 0.025, 3)
        false_accepts = sum(
            row["best_vector_distance"] is not None
            and row["best_vector_distance"] <= threshold
            for row in unanswerable
        )
        false_refusals = sum(
            row["best_vector_distance"] is None
            or row["best_vector_distance"] > threshold
            for row in answerable
        )
        output.append(
            {
                "threshold": threshold,
                "false_accept_rate": _wilson(false_accepts, len(unanswerable)),
                "false_refusal_rate": _wilson(false_refusals, len(answerable)),
            }
        )
    return output


def _kind_breakdown(rows: Sequence[dict[str, Any]]) -> dict[str, Any]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        kind = str(row["category"]).removeprefix("unanswerable_")
        kind = "near-miss" if kind == "near" else kind
        grouped.setdefault(kind, []).append(row)
    return {
        kind: {
            "refused": sum(bool(row["guard_refused"]) for row in subset),
            "n": len(subset),
            "refusal_rate": _wilson(
                sum(bool(row["guard_refused"]) for row in subset),
                len(subset),
            ),
        }
        for kind, subset in sorted(grouped.items())
    }


def _score_scope(
    rows: Sequence[dict[str, Any]],
    rows_by_repo: Mapping[str, Sequence[dict[str, Any]]],
    repo_ids: Sequence[str],
) -> dict[str, Any]:
    answerable = [row for row in rows if not str(row["category"]).startswith("unanswerable")]
    unanswerable = [row for row in rows if row not in answerable]
    hits: dict[str, Any] = {}
    for k in (1, 3, 5, 10, 20):
        count = sum(
            span_hit_at_k([row["ranked_chunks"]], [row["relevant_spans"]], k)
            for row in answerable
        )
        hits[f"hit_at_{k}"] = _wilson(count, len(answerable))
    answerable_by_repo = {
        repo_id: [
            row
            for row in rows_by_repo[repo_id]
            if not str(row["category"]).startswith("unanswerable")
        ]
        for repo_id in repo_ids
    }
    retrieval = dict(hits)
    for field in (
        "mrr_at_5",
        "ndcg_at_5",
        "ndcg_at_10",
        "recall_at_20",
        "context_precision_at_5",
    ):
        retrieval[field] = _bootstrap_mean(answerable_by_repo, field, repo_ids)

    labels = [not str(row["category"]).startswith("unanswerable") for row in rows]
    refused = [bool(row["guard_refused"]) for row in rows]
    confusion = guard_confusion(labels, [not value for value in refused])
    refusal = refusal_precision_recall(labels, refused)
    precision_n = int(refusal["true_positive"]) + int(refusal["false_positive"])
    recall_n = int(refusal["true_positive"]) + int(refusal["false_negative"])
    guard = {
        "false_accept_rate": _wilson(
            confusion["false_accept"], len(unanswerable)
        ),
        "correct_refusal_rate": _wilson(
            confusion["true_refusal"], len(unanswerable)
        ),
        "false_refusal_rate": _wilson(
            confusion["false_refusal"], len(answerable)
        ),
        "refusal_precision": {
            **_wilson(int(refusal["true_positive"]), precision_n),
            "value": refusal["precision"],
        },
        "refusal_recall": {
            **_wilson(int(refusal["true_positive"]), recall_n),
            "value": refusal["recall"],
        },
        "auroc": _auroc_metric(rows_by_repo, repo_ids),
        "threshold_sweep": _threshold_sweep(rows),
        "unanswerable_kind": _kind_breakdown(unanswerable),
        "confusion": confusion,
    }
    return {
        "n": len(rows),
        "answerable_n": len(answerable),
        "unanswerable_n": len(unanswerable),
        "retrieval": retrieval,
        "guard": guard,
    }


def build_scorecard(
    export: Mapping[str, Any],
    *,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Validate a development export and calculate the registered scorecard."""

    manifest = load_manifest(manifest_path, root=root)
    raw_by_repo = _validate_export(export, manifest, manifest_path, root)
    entries = {entry["id"]: entry for entry in manifest["repositories"]}
    scored_by_repo: dict[str, list[dict[str, Any]]] = {}
    per_repository: dict[str, Any] = {}
    for repo_id in V1_REPOSITORIES:
        fixture = load_fixture(root / entries[repo_id]["fixture"]["path"])
        fixture_chunks = fixture["chunks"]
        scored = []
        for row in raw_by_repo[repo_id]:
            if str(row["category"]).startswith("unanswerable"):
                scored.append(row)
                continue
            spans = row["relevant_spans"]
            ranked = row["ranked_chunks"]
            row.update(
                {
                    f"ndcg_at_{k}": ndcg_at_k(ranked, spans, fixture_chunks, k)
                    for k in (5, 10)
                }
            )
            row["recall_at_20"] = recall_at_k(ranked, spans, 20)
            row["context_precision_at_5"] = context_precision_at_k(ranked, spans, 5)
            row["mrr_at_5"] = (
                1 / rank
                if (rank := first_relevant_span_rank(ranked[:5], spans)) is not None
                else 0.0
            )
            row.update(
                {
                    f"hit_at_{k}": int(span_hit_at_k([ranked], [spans], k))
                    for k in (1, 3, 5, 10, 20)
                }
            )
            scored.append(row)
        scored_by_repo[repo_id] = scored
        per_repository[repo_id] = _score_scope(
            scored,
            {repo_id: scored},
            [repo_id],
        )

    pooled_rows = [row for repo_id in V1_REPOSITORIES for row in scored_by_repo[repo_id]]
    pooled = _score_scope(pooled_rows, scored_by_repo, V1_REPOSITORIES)
    export_metadata = export["metadata"]
    code_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "metadata": {
            "dataset_version": "v1",
            "repository_ids": list(V1_REPOSITORIES),
            "n": len(pooled_rows),
            "seed": BOOTSTRAP_SEED,
            "resamples": BOOTSTRAP_RESAMPLES,
            "git_commit": export_metadata["git_commit"],
            "scorecard_git_commit": code_commit,
            "protocol": PROTOCOL_PATH,
            "split": export_metadata["split"],
            "manifest_sha256": export_metadata["manifest_sha256"],
            "run_date": datetime.now(UTC).date().isoformat(),
        },
        "per_repository": per_repository,
        "pooled": pooled,
    }


def verify_registered_crosscheck(
    scorecard: Mapping[str, Any],
    *,
    results_path: Path | None = None,
) -> list[tuple[str, str, str]]:
    """Compare computed controls with the registered BM25 development artifact."""

    artifact_path = results_path or ROOT / "evaluation/experiments/bm25/results.json"
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    metadata = artifact["metadata"]
    if metadata.get("split") != "development" or metadata.get("held_out_used") is not False:
        raise ValueError("Registered BM25 cross-check artifact is not development-only")
    expected_repositories = list(V1_REPOSITORIES)
    if sorted(metadata.get("repositories", [])) != expected_repositories:
        raise ValueError("Registered BM25 cross-check repository set does not match v1")
    control = artifact["pooled"]["methods"]["control"]
    computed_retrieval = scorecard["pooled"]["retrieval"]
    computed_guard = scorecard["pooled"]["guard"]["confusion"]
    expected_guard = {
        "correct_refusals": sum(
            row["guard"]["control"]["insufficient"]
            for row in artifact["per_repository"].values()
        ),
        "false_accepts": sum(
            row["guard"]["control"]["sufficient"]
            for row in artifact["per_repository"].values()
        ),
    }
    comparisons = [
        ("Hit@1", f"{control['hit_at_1_successes']}/33",
         f"{computed_retrieval['hit_at_1']['successes']}/{computed_retrieval['hit_at_1']['n']}"),
        ("Hit@3", f"{control['hit_at_3_successes']}/33",
         f"{computed_retrieval['hit_at_3']['successes']}/{computed_retrieval['hit_at_3']['n']}"),
        ("Hit@5", f"{control['hit_at_5_successes']}/33",
         f"{computed_retrieval['hit_at_5']['successes']}/{computed_retrieval['hit_at_5']['n']}"),
        ("MRR", f"{control['mrr']:.6f}", f"{computed_retrieval['mrr_at_5']['value']:.6f}"),
        ("Correct refusals", f"{expected_guard['correct_refusals']}/15",
         f"{computed_guard['true_refusal']}/15"),
        ("False accepts", f"{expected_guard['false_accepts']}/15",
         f"{computed_guard['false_accept']}/15"),
    ]
    for label, expected, computed in comparisons:
        print(f"{label}: expected {expected}; computed {computed}")
    expected_counts = (19, 26, 28, 9, 6)
    computed_counts = (
        computed_retrieval["hit_at_1"]["successes"],
        computed_retrieval["hit_at_3"]["successes"],
        computed_retrieval["hit_at_5"]["successes"],
        computed_guard["true_refusal"],
        computed_guard["false_accept"],
    )
    if expected_counts != computed_counts:
        raise ValueError("Registered scorecard count cross-check failed")
    if (
        control["hit_at_1_successes"] != 19
        or control["hit_at_3_successes"] != 26
        or control["hit_at_5_successes"] != 28
        or abs(float(control["mrr"]) - 0.6737373737373737) > 1e-12
        or abs(float(computed_retrieval["mrr_at_5"]["value"]) - float(control["mrr"]))
        > 1e-12
        or expected_guard != {"correct_refusals": 9, "false_accepts": 6}
    ):
        raise ValueError("Registered BM25 cross-check values differ from protocol 16")
    return comparisons


def write_scorecard(
    input_path: Path,
    output_path: Path,
    *,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Read an export, compute the scorecard, and persist the JSON."""

    export = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(export, Mapping):
        raise ValueError("Rankings export must contain a JSON object")
    scorecard = build_scorecard(export, manifest_path=manifest_path, root=root)
    verify_registered_crosscheck(scorecard)
    scorecard["metadata"]["rankings_export"] = str(input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(scorecard, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return scorecard
