"""Deterministic preparation and analysis for the chunking comparison."""

from __future__ import annotations

import asyncio
import hashlib
import json
import math
import random
from collections import Counter
from collections.abc import Awaitable, Callable, Mapping, Sequence
from pathlib import Path, PurePosixPath
from statistics import median
from typing import Any

from app.retrieval.chunking import (
    EMBEDDING_TEXT_VERSION,
    describe_chunker,
)
from app.secret_scan import find_secret
from evaluation.build_fixture import write_fixture
from evaluation.chunk_experiments import (
    CANDIDATE_STRATEGIES,
    candidate_chunk_specs,
    candidate_embedding_text,
    get_candidate_strategy,
)
from evaluation.manifest import (
    MANIFEST_PATH,
    load_manifest,
    manifest_root,
    sha256_file,
)
from evaluation.stats import exact_sign_test
from scripts.ingest_repo import iter_python_files

ROOT = Path(__file__).resolve().parents[1]
EXPERIMENT_ROOT = ROOT / "evaluation" / "experiments" / "chunking"
PROTOCOL_PATH = EXPERIMENT_ROOT / "protocol.json"
SOURCE_ROOT = ROOT / "evaluation" / "_snapshot" / "chunking-sources"
CACHE_ROOT = ROOT / "evaluation" / "cache" / "chunk_embeddings"
STRATEGIES = (
    "s0_lines_60_10",
    "s1_lines_100_20",
    "s2_ast_v1",
    "s3_ast_v1_embed_text",
)
S0_STRATEGY = STRATEGIES[0]
ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}


def _text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def discover_sources(
    root: Path,
    exclude_prefixes: Sequence[str] = (),
) -> dict[str, str]:
    """Read Python files deterministically, using POSIX-relative paths."""

    excluded = tuple(prefix.strip("/") for prefix in exclude_prefixes)
    sources: dict[str, str] = {}
    for file_path in sorted(iter_python_files(root)):
        relative_path = file_path.relative_to(root).as_posix()
        if any(
            relative_path == prefix or relative_path.startswith(prefix + "/")
            for prefix in excluded
        ):
            continue
        sources[relative_path] = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    return sources


def build_strategy_chunks_and_count(
    strategy: str,
    sources: Mapping[str, str],
) -> tuple[list[dict[str, Any]], int]:
    """Build chunks and return the count excluded by secret scanning."""

    if strategy not in CANDIDATE_STRATEGIES:
        get_candidate_strategy(strategy)
    chunks: list[dict[str, Any]] = []
    secret_skipped_count = 0
    for file_path in sorted(sources):
        source = sources[file_path]
        for spec in candidate_chunk_specs(strategy, source):
            if find_secret(spec.content) is not None:
                secret_skipped_count += 1
                continue
            chunks.append(
                {
                    "file_path": file_path,
                    "line_start": spec.line_start,
                    "line_end": spec.line_end,
                    "content": spec.content,
                    "embedding_text": candidate_embedding_text(
                        strategy,
                        spec,
                        file_path,
                    ),
                    "symbol": spec.symbol,
                    "kind": spec.kind,
                }
            )
    return chunks, secret_skipped_count


def build_strategy_chunks(
    strategy: str,
    sources: Mapping[str, str],
) -> list[dict[str, Any]]:
    """Build secret-free chunks and their corresponding embedding text."""

    chunks, _ = build_strategy_chunks_and_count(strategy, sources)
    return chunks


def _chunk_tuples(chunks: Sequence[Mapping[str, Any]]) -> list[tuple[str, int, int, str]]:
    return sorted(
        (
            str(chunk["file_path"]),
            int(chunk["line_start"]),
            int(chunk["line_end"]),
            str(chunk["content"]),
        )
        for chunk in chunks
    )


def check_s0_reproduces_baseline(
    chunks: Sequence[Mapping[str, Any]],
    baseline_fixture: Mapping[str, Any],
) -> None:
    """Raise with a short diff if S0 chunks differ from the committed fixture."""

    actual = _chunk_tuples(chunks)
    expected = _chunk_tuples(baseline_fixture["chunks"])
    actual_counts = Counter(actual)
    expected_counts = Counter(expected)
    missing = list((expected_counts - actual_counts).elements())
    extra = list((actual_counts - expected_counts).elements())
    if not missing and not extra:
        return

    differences = [
        *(("missing from candidate", item) for item in missing),
        *(("not in baseline", item) for item in extra),
    ]
    lines = [
        f"{difference}: {file_path}:{line_start}-{line_end} "
        f"content={content[:100]!r}"
        for difference, (file_path, line_start, line_end, content) in differences[:5]
    ]
    raise RuntimeError(
        "S0 does not reproduce the committed baseline; first differences:\n"
        + "\n".join(lines)
    )


def _fixture_values(value: Any) -> list[Mapping[str, Any]]:
    if isinstance(value, Mapping):
        if isinstance(value.get("chunks"), list):
            return [value]
        fixtures: list[Mapping[str, Any]] = []
        for nested in value.values():
            fixtures.extend(_fixture_values(nested))
        return fixtures
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if all(
            isinstance(item, Mapping) and "embedding_text" in item
            for item in value
        ):
            return [{"chunks": value}]
        fixtures = []
        for nested in value:
            fixtures.extend(_fixture_values(nested))
        return fixtures
    return []


def _read_cache_vector(path: Path) -> list[float]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list) or any(
        isinstance(item, bool)
        or not isinstance(item, (int, float))
        or not math.isfinite(item)
        for item in value
    ):
        raise ValueError(f"Invalid embedding cache vector: {path}")
    return [float(item) for item in value]


def plan_embeddings(
    all_chunks_by_strategy: Mapping[str, Any],
    baseline_fixtures: Mapping[str, Any] | Sequence[Any],
    cache_dir: Path,
) -> list[str]:
    """Return unique not-yet-cached embedding texts, ordered by SHA-256."""

    baseline_contents = {
        str(chunk["content"])
        for fixture in _fixture_values(baseline_fixtures)
        for chunk in fixture["chunks"]
    }
    texts_by_hash: dict[str, str] = {}
    for fixture_chunks in _fixture_values(all_chunks_by_strategy):
        for chunk in fixture_chunks.get("chunks", []):
            text = chunk.get("embedding_text")
            if not isinstance(text, str):
                raise ValueError("Every candidate chunk needs embedding_text")
            if text in baseline_contents:
                continue
            digest = _text_hash(text)
            cache_path = cache_dir / f"{digest}.json"
            if cache_path.is_file():
                _read_cache_vector(cache_path)
                continue
            texts_by_hash[digest] = text
    return [texts_by_hash[digest] for digest in sorted(texts_by_hash)]


def load_protocol(path: Path = PROTOCOL_PATH) -> dict[str, Any]:
    """Load the committed, pre-embedding experiment protocol."""

    try:
        protocol = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load chunking protocol {path}: {exc}") from exc
    if not isinstance(protocol, dict):
        raise ValueError("Chunking protocol must contain a JSON object")
    return protocol


async def embed_missing(
    texts: Sequence[str],
    cache_dir: Path,
    embed_fn: Callable[[list[str]], Awaitable[list[list[float]]]],
    *,
    batch_delay_seconds: float = 0.0,
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep,
) -> None:
    """Embed bounded sequential batches and cache each returned vector at once."""

    protocol = load_protocol()
    config = protocol["embedding"]
    batch_size = int(config["batch_size"])
    max_texts = int(config["max_texts"])
    max_batch_requests = int(config["max_batch_requests"])
    if batch_size < 1:
        raise ValueError("Protocol embedding batch_size must be positive")
    request_count = math.ceil(len(texts) / batch_size) if texts else 0
    if len(texts) > max_texts or request_count > max_batch_requests:
        raise ValueError(
            f"Embedding plan exceeds protocol caps: {len(texts)} texts, "
            f"{request_count} batch requests; caps are {max_texts} texts and "
            f"{max_batch_requests} requests"
        )
    if any(not isinstance(text, str) for text in texts):
        raise ValueError("Embedding texts must be strings")

    cache_dir.mkdir(parents=True, exist_ok=True)
    batches = [
        list(texts[offset : offset + batch_size])
        for offset in range(0, len(texts), batch_size)
    ]
    for batch_index, batch in enumerate(batches):
        vectors = await embed_fn(batch)
        if len(vectors) != len(batch):
            raise ValueError(
                f"Embedding function returned {len(vectors)} vectors "
                f"for {len(batch)} texts"
            )
        for text, vector in zip(batch, vectors):
            if any(
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                for value in vector
            ):
                raise ValueError("Embedding function returned an invalid vector")
            (cache_dir / f"{_text_hash(text)}.json").write_text(
                json.dumps(vector, separators=(",", ":")),
                encoding="utf-8",
            )
        if batch_delay_seconds > 0 and batch_index < len(batches) - 1:
            await sleep(batch_delay_seconds)


def write_protocol(
    path: Path = PROTOCOL_PATH,
    *,
    manifest_path: Path = MANIFEST_PATH,
    root: Path = ROOT,
) -> dict[str, Any]:
    """Recreate the deterministic experiment protocol from the current manifest."""

    asset_root = manifest_root(manifest_path) if root == ROOT else root
    manifest = load_manifest(manifest_path, root=asset_root)
    repositories = manifest["repositories"]
    baseline_artifacts = {
        entry["id"]: sha256_file(asset_root / entry["fixture"]["path"])
        for entry in repositories
    }
    protocol = {
        "schema_version": 1,
        "strategies": list(STRATEGIES),
        "simplicity_order": list(STRATEGIES),
        "repositories": [entry["id"] for entry in repositories],
        "selection_split": "development",
        "label_type": "spans",
        "rule": {
            "max_repo_hit5_loss": 1,
            "max_repo_mrr_loss": 0.03,
            "min_pooled_delta_mrr": 0.03,
            "max_cost_ratio_mean": 1.5,
            "max_cost_ratio_p95": 1.5,
            "tie_epsilon": 1e-9,
        },
        "statistics": {
            "bootstrap_seed": 20261026,
            "bootstrap_resamples": 10000,
            "bootstrap_interval": 0.95,
        },
        "embedding": {
            "model": "models/gemini-embedding-001",
            "dimension": 768,
            "batch_size": 50,
            "max_texts": 700,
            "max_batch_requests": 20,
            "reuse_baseline_vectors_by_text_hash": True,
        },
        "chunkers": {
            "lines": describe_chunker("lines"),
            "ast": describe_chunker("ast"),
            "embedding_text_version": EMBEDDING_TEXT_VERSION,
        },
        "baseline_artifacts": baseline_artifacts,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(protocol, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return protocol


def _line_chunker_description(strategy: str) -> dict[str, str | int]:
    candidate = get_candidate_strategy(strategy)
    if candidate.chunker == "lines":
        return {
            "chunker": "lines",
            "size": candidate.line_size or 60,
            "overlap": candidate.line_overlap or 10,
        }
    return describe_chunker("ast")


def build_candidate_fixture(
    repo_id: str,
    strategy: str,
    chunks: Sequence[Mapping[str, Any]],
    baseline_fixture: Mapping[str, Any],
    vectors: Mapping[str, Sequence[float]],
    max_bytes: int,
    *,
    output_root: Path = ROOT,
    secret_skipped_count: int = 0,
) -> tuple[str, int]:
    """Write a deterministic candidate fixture, retaining raw chunk contents."""

    candidate = get_candidate_strategy(strategy)
    fixture_chunks = []
    for chunk in sorted(
        chunks,
        key=lambda value: (
            str(value["file_path"]),
            int(value["line_start"]),
            int(value["line_end"]),
        ),
    ):
        digest = _text_hash(str(chunk["embedding_text"]))
        if digest not in vectors:
            raise ValueError(
                f"Missing embedding vector for text hash {digest}"
            )
        fixture_chunks.append(
            {
                "file_path": str(chunk["file_path"]),
                "line_start": int(chunk["line_start"]),
                "line_end": int(chunk["line_end"]),
                "content": str(chunk["content"]),
                "embedding": [
                    round(float(value), 6) for value in vectors[digest]
                ],
            }
        )

    protocol = load_protocol()
    fixture = {
        "meta": {
            "strategy": strategy,
            "chunker": _line_chunker_description(strategy),
            "embedding_text_version": (
                candidate.embedding_text
                if candidate.embedding_text != "raw"
                else "raw"
            ),
            "pinned_sha": baseline_fixture["meta"]["pinned_sha"],
            "embedding_model": protocol["embedding"]["model"],
            "chunk_count": len(fixture_chunks),
            "question_count": len(baseline_fixture["queries"]),
            "secret_skipped_count": secret_skipped_count,
        },
        "chunks": fixture_chunks,
        "queries": dict(baseline_fixture["queries"]),
    }
    path = (
        output_root
        / "evaluation"
        / "experiments"
        / "chunking"
        / "fixtures"
        / repo_id
        / f"{strategy}.json.gz"
    )
    size = write_fixture(fixture, path, max_bytes)
    return hashlib.sha256(path.read_bytes()).hexdigest(), size


def _nearest_rank(values: Sequence[float], percentile: float) -> float | None:
    if not values:
        return None
    if not 0 < percentile <= 1:
        raise ValueError("percentile must be in (0, 1]")
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def _span_lines(spans: Sequence[Mapping[str, Any]]) -> set[tuple[str, int]]:
    lines: set[tuple[str, int]] = set()
    for span in spans:
        path = str(span["file_path"])
        start = int(span["line_start"])
        end = int(span["line_end"])
        if start < 1 or end < start:
            raise ValueError(f"Invalid question span for {path}")
        lines.update((path, line) for line in range(start, end + 1))
    return lines


def _retrieved_lines(
    retrieved: Sequence[Mapping[str, Any]],
) -> set[tuple[str, int]]:
    lines: set[tuple[str, int]] = set()
    for result in retrieved:
        path = str(result["file_path"])
        start = int(result["line_start"])
        end = int(result["line_end"])
        if start < 1 or end < start:
            raise ValueError(f"Invalid retrieved range for {path}")
        lines.update((path, line) for line in range(start, end + 1))
    return lines


def _source_character_cost(
    lines: set[tuple[str, int]],
    sources: Mapping[str, str],
) -> int:
    by_path: dict[str, list[str]] = {}
    cost = 0
    for path, line_number in sorted(lines):
        if path not in by_path:
            if path not in sources:
                raise ValueError(f"Retrieved source is unavailable: {path}")
            by_path[path] = sources[path].splitlines()
        source_lines = by_path[path]
        if line_number <= len(source_lines):
            cost += len(source_lines[line_number - 1]) + 1
    return cost


def _is_test_path(file_path: str) -> bool:
    path = PurePosixPath(file_path)
    basename = path.name.casefold()
    return (
        any(part.casefold() in {"test", "tests"} for part in path.parts)
        or basename.startswith("test_")
        or basename.endswith("_test.py")
    )


def _cosine_distance(first: Sequence[float], second: Sequence[float]) -> float:
    if len(first) != len(second):
        raise ValueError("Query and chunk embedding dimensions do not match")
    first_norm = math.sqrt(sum(float(value) ** 2 for value in first))
    second_norm = math.sqrt(sum(float(value) ** 2 for value in second))
    if first_norm == 0 or second_norm == 0:
        raise ValueError("Cosine distance is undefined for a zero embedding")
    similarity = sum(
        float(left) * float(right) for left, right in zip(first, second)
    ) / (first_norm * second_norm)
    return 1.0 - max(-1.0, min(1.0, similarity))


def _distance_summary(values: Sequence[float]) -> dict[str, float | None]:
    if not values:
        return {"min": None, "median": None, "max": None}
    return {
        "min": min(values),
        "median": float(median(values)),
        "max": max(values),
    }


def _summarize_question_metrics(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    answerable = [
        record
        for record in records
        if record["category"] in ANSWERABLE_CATEGORIES
    ]
    count = len(answerable)
    retrieval: dict[str, Any] = {
        "count": count,
        "mrr": (
            sum(float(record["reciprocal_rank"]) for record in answerable) / count
            if count
            else 0.0
        ),
    }
    for cutoff in (1, 3, 5):
        successes = sum(bool(record[f"hit_at_{cutoff}"]) for record in answerable)
        retrieval[f"hit_at_{cutoff}"] = {
            "successes": successes,
            "rate": successes / count if count else 0.0,
        }

    by_category = {}
    for category in ("direct", "paraphrased"):
        category_records = [
            record for record in answerable if record["category"] == category
        ]
        category_count = len(category_records)
        category_retrieval: dict[str, Any] = {
            "count": category_count,
            "mrr": (
                sum(float(record["reciprocal_rank"]) for record in category_records)
                / category_count
                if category_count
                else 0.0
            ),
        }
        for cutoff in (1, 3, 5):
            successes = sum(
                bool(record[f"hit_at_{cutoff}"]) for record in category_records
            )
            category_retrieval[f"hit_at_{cutoff}"] = {
                "successes": successes,
                "rate": successes / category_count if category_count else 0.0,
            }
        by_category[category] = category_retrieval

    costs = [int(record["cost_chars"]) for record in answerable]
    label_lines = sum(int(record["label_line_count"]) for record in answerable)
    covered_lines = sum(int(record["covered_label_line_count"]) for record in answerable)
    retrieved_lines = sum(int(record["retrieved_line_count"]) for record in answerable)
    top1_retrieved_lines = sum(
        int(record["top1_retrieved_line_count"]) for record in answerable
    )
    test_results = sum(int(record["test_result_count"]) for record in answerable)
    total_results = sum(int(record["result_count"]) for record in answerable)
    nearest_answerable = [
        float(record["nearest_distance"])
        for record in answerable
        if record["nearest_distance"] is not None
    ]
    nearest_unanswerable = [
        float(record["nearest_distance"])
        for record in records
        if record["category"].startswith("unanswerable")
        and record["nearest_distance"] is not None
    ]
    return {
        "retrieval": retrieval,
        "by_category": by_category,
        "cost": {
            "count": len(costs),
            "mean": sum(costs) / len(costs) if costs else 0.0,
            "p95": _nearest_rank(costs, 0.95) if costs else 0.0,
        },
        "coverage_at_5": {
            "covered_label_lines": covered_lines,
            "label_lines": label_lines,
            "rate": covered_lines / label_lines if label_lines else 0.0,
        },
        "density_at_5": {
            "covered_label_lines": covered_lines,
            "retrieved_lines": retrieved_lines,
            "rate": covered_lines / retrieved_lines if retrieved_lines else 0.0,
        },
        "top1_density": {
            "covered_label_lines": sum(
                int(record["top1_covered_label_line_count"])
                for record in answerable
            ),
            "retrieved_lines": top1_retrieved_lines,
            "rate": (
                sum(
                    int(record["top1_covered_label_line_count"])
                    for record in answerable
                )
                / top1_retrieved_lines
                if top1_retrieved_lines
                else 0.0
            ),
        },
        "test_share": {
            "test_results": test_results,
            "results": total_results,
            "rate": test_results / total_results if total_results else 0.0,
        },
        "nearest_chunk_cosine_distance": {
            "answerable": _distance_summary(nearest_answerable),
            "unanswerable": _distance_summary(nearest_unanswerable),
        },
    }


def compute_metrics(
    report: Mapping[str, Any],
    sources: Mapping[str, str],
    questions: Sequence[Mapping[str, Any]],
    fixture: Mapping[str, Any],
    fixture_bytes: int = 0,
) -> dict[str, Any]:
    """Compute span-first retrieval, context, cost, chunk, and distance metrics."""

    question_by_id = {str(question["id"]): question for question in questions}
    fixture_chunks = fixture["chunks"]
    chunk_embeddings = [
        chunk["embedding"]
        for chunk in fixture_chunks
    ]
    line_lengths = [
        int(chunk["line_end"]) - int(chunk["line_start"]) + 1
        for chunk in fixture_chunks
    ]
    question_metrics: list[dict[str, Any]] = []
    for record in report["questions"]:
        question_id = str(record["id"])
        if question_id not in question_by_id:
            raise ValueError(f"Retrieval report has unknown question {question_id}")
        question = question_by_id[question_id]
        retrieved = record.get("retrieved")
        if not isinstance(retrieved, list):
            raise ValueError(
                f"Retrieval report lacks retrieved results for {question_id}"
            )
        retrieved_top5 = retrieved[:5]
        top1 = retrieved_top5[:1]
        label_lines = _span_lines(question.get("relevant_spans", []))
        retrieved_line_set = _retrieved_lines(retrieved_top5)
        top1_line_set = _retrieved_lines(top1)
        query_vector = fixture["queries"].get(question_id)
        if query_vector is None:
            raise ValueError(f"Fixture lacks query embedding for {question_id}")
        nearest_distance = None
        if query_vector is not None and chunk_embeddings:
            nearest_distance = min(
                _cosine_distance(query_vector, embedding)
                for embedding in chunk_embeddings
            )
        covered_lines = label_lines & retrieved_line_set
        top1_covered_lines = label_lines & top1_line_set
        source_chars = _source_character_cost(retrieved_line_set, sources)
        question_metrics.append(
            {
                "id": question_id,
                "category": str(question["category"]),
                "reciprocal_rank": (
                    1 / int(record["span_rank"])
                    if record.get("span_rank") is not None
                    else 0.0
                ),
                "hit_at_1": bool(record.get("span_hits", {}).get("1", False)),
                "hit_at_3": bool(record.get("span_hits", {}).get("3", False)),
                "hit_at_5": bool(record.get("span_hits", {}).get("5", False)),
                "cost_chars": source_chars,
                "label_line_count": len(label_lines),
                "covered_label_line_count": len(covered_lines),
                "retrieved_line_count": len(retrieved_line_set),
                "top1_covered_label_line_count": len(top1_covered_lines),
                "top1_retrieved_line_count": len(top1_line_set),
                "test_result_count": sum(
                    _is_test_path(str(result["file_path"]))
                    for result in retrieved_top5
                ),
                "result_count": len(retrieved_top5),
                "nearest_distance": nearest_distance,
            }
        )

    summary = _summarize_question_metrics(question_metrics)
    return {
        "repo_id": str(report["metadata"]["repo_id"]),
        "question_count": len(question_metrics),
        **summary,
        "chunk_statistics": {
            "count": len(fixture_chunks),
            "line_length": {
                "min": min(line_lengths) if line_lengths else None,
                "median": float(median(line_lengths)) if line_lengths else None,
                "p95": _nearest_rank(line_lengths, 0.95),
                "max": max(line_lengths) if line_lengths else None,
            },
            "fixture_bytes": fixture_bytes,
        },
        "_chunk_line_lengths": line_lengths,
        "question_metrics": question_metrics,
    }


def _pooled_metrics(
    repository_metrics: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    records = [
        record
        for metrics in repository_metrics.values()
        for record in metrics["question_metrics"]
    ]
    pooled = _summarize_question_metrics(records)
    chunk_lengths = [
        int(length)
        for metrics in repository_metrics.values()
        for length in metrics["_chunk_line_lengths"]
    ]
    pooled["chunk_statistics"] = {
        "count": sum(
            int(metrics["chunk_statistics"]["count"])
            for metrics in repository_metrics.values()
        ),
        "line_length": {
            "min": min(chunk_lengths) if chunk_lengths else None,
            "median": float(median(chunk_lengths)) if chunk_lengths else None,
            "p95": _nearest_rank(chunk_lengths, 0.95),
            "max": max(chunk_lengths) if chunk_lengths else None,
        },
        "fixture_bytes": sum(
            int(metrics["chunk_statistics"]["fixture_bytes"])
            for metrics in repository_metrics.values()
        ),
    }
    pooled["question_count"] = len(records)
    pooled["repo_count"] = len(repository_metrics)
    pooled["question_metrics"] = records
    return pooled


def paired_statistics(
    candidate_rr: Sequence[float],
    s0_rr: Sequence[float],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Compare paired reciprocal ranks and bootstrap pooled delta-MRR."""

    if len(candidate_rr) != len(s0_rr):
        raise ValueError("paired reciprocal-rank inputs must have equal lengths")
    deltas = [
        float(candidate) - float(baseline)
        for candidate, baseline in zip(candidate_rr, s0_rr)
    ]
    if any(not math.isfinite(value) for value in deltas):
        raise ValueError("reciprocal ranks must be finite")
    wins = sum(delta > 0 for delta in deltas)
    losses = sum(delta < 0 for delta in deltas)
    ties = len(deltas) - wins - losses
    delta_mrr = sum(deltas) / len(deltas) if deltas else 0.0
    stats = protocol["statistics"]
    resamples = int(stats["bootstrap_resamples"])
    interval = float(stats["bootstrap_interval"])
    if resamples < 1 or not 0 < interval < 1:
        raise ValueError("Invalid bootstrap protocol settings")
    rng = random.Random(int(stats["bootstrap_seed"]))
    bootstrap_means = []
    if deltas:
        for _ in range(resamples):
            sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
            bootstrap_means.append(sum(sample) / len(sample))
    tail = (1.0 - interval) / 2

    def percentile(values: Sequence[float], q: float) -> float:
        ordered = sorted(values)
        position = (len(ordered) - 1) * q
        lower = math.floor(position)
        upper = math.ceil(position)
        if lower == upper:
            return ordered[lower]
        return ordered[lower] + (ordered[upper] - ordered[lower]) * (
            position - lower
        )

    confidence_interval = (
        [percentile(bootstrap_means, tail), percentile(bootstrap_means, 1 - tail)]
        if bootstrap_means
        else [0.0, 0.0]
    )
    return {
        "wins": wins,
        "losses": losses,
        "ties": ties,
        "sign_test_p_value": exact_sign_test(wins, losses),
        "delta_mrr": delta_mrr,
        "bootstrap_interval": confidence_interval,
        "bootstrap_resamples": resamples,
        "bootstrap_seed": int(stats["bootstrap_seed"]),
    }


def select_winner(
    per_strategy_results: Mapping[str, Mapping[str, Any]],
    protocol: Mapping[str, Any],
) -> dict[str, Any]:
    """Apply every precommitted S0-relative condition and choose a winner."""

    s0 = per_strategy_results[S0_STRATEGY]
    rule = protocol["rule"]
    candidate_conditions: dict[str, dict[str, bool]] = {}
    qualifiers: list[str] = []
    condition_names = (
        "repository_hit5_loss",
        "repository_mrr_loss",
        "pooled_mrr_gain",
        "pooled_mean_cost",
        "pooled_p95_cost",
    )

    for strategy in protocol["strategies"]:
        if strategy == S0_STRATEGY:
            continue
        candidate = per_strategy_results[strategy]
        expected_repositories = set(protocol["repositories"])
        candidate_repositories = set(candidate["repositories"])
        same_repositories = (
            candidate_repositories == expected_repositories
            and set(s0["repositories"]) == expected_repositories
        )
        hit5_pass = same_repositories and all(
            int(s0["repositories"][repo_id]["retrieval"]["hit_at_5"]["successes"])
            - int(candidate["repositories"][repo_id]["retrieval"]["hit_at_5"]["successes"])
            <= int(rule["max_repo_hit5_loss"])
            for repo_id in expected_repositories
        )
        repo_mrr_pass = same_repositories and all(
            float(candidate["repositories"][repo_id]["retrieval"]["mrr"])
            >= float(s0["repositories"][repo_id]["retrieval"]["mrr"])
            - float(rule["max_repo_mrr_loss"])
            for repo_id in expected_repositories
        )
        pooled_mrr_pass = (
            float(candidate["pooled"]["retrieval"]["mrr"])
            - float(s0["pooled"]["retrieval"]["mrr"])
            >= float(rule["min_pooled_delta_mrr"])
        )

        def cost_pass(candidate_value: float, baseline_value: float, ratio: float) -> bool:
            if baseline_value == 0:
                return candidate_value == 0
            return candidate_value <= ratio * baseline_value

        mean_cost_pass = cost_pass(
            float(candidate["pooled"]["cost"]["mean"]),
            float(s0["pooled"]["cost"]["mean"]),
            float(rule["max_cost_ratio_mean"]),
        )
        p95_cost_pass = cost_pass(
            float(candidate["pooled"]["cost"]["p95"]),
            float(s0["pooled"]["cost"]["p95"]),
            float(rule["max_cost_ratio_p95"]),
        )
        conditions = dict(
            zip(
                condition_names,
                (
                    hit5_pass,
                    repo_mrr_pass,
                    pooled_mrr_pass,
                    mean_cost_pass,
                    p95_cost_pass,
                ),
            )
        )
        conditions["qualifies"] = all(conditions.values())
        candidate_conditions[strategy] = conditions
        if conditions["qualifies"]:
            qualifiers.append(strategy)

    if not qualifiers:
        winner = S0_STRATEGY
        status = "S0 retained"
    else:
        best_mrr = max(
            float(per_strategy_results[strategy]["pooled"]["retrieval"]["mrr"])
            for strategy in qualifiers
        )
        tied = [
            strategy
            for strategy in qualifiers
            if best_mrr
            - float(per_strategy_results[strategy]["pooled"]["retrieval"]["mrr"])
            <= float(rule["tie_epsilon"])
        ]
        simplicity_rank = {
            strategy: index
            for index, strategy in enumerate(protocol["simplicity_order"])
        }
        winner = min(tied, key=lambda strategy: simplicity_rank[strategy])
        status = "candidate selected"
    return {
        "winner": winner,
        "status": status,
        "qualifiers": qualifiers,
        "conditions": candidate_conditions,
        "rules": dict(rule),
        "simplicity_order": list(protocol["simplicity_order"]),
    }
