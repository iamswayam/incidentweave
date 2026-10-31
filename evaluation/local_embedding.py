"""Pure helpers for the registered local embedding-model comparison."""

from __future__ import annotations

import hashlib
import math
import random
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from statistics import median
from typing import Any, Literal

from evaluation.metrics import first_relevant_rank
from evaluation.stats import exact_sign_test

EXPERIMENT_VERSION = "local_embedding_v1"
FASTEMBED_VERSION = "0.9.1"
TOP_K = 5
RRF_CONSTANT = 60
BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_INTERVAL = 0.95
GUARD_DISTANCE_THRESHOLD = 0.5
ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}
VectorRole = Literal["document", "query"]


@dataclass(frozen=True)
class EmbeddingModel:
    """A preregistered FastEmbed model and its pinned reporting metadata."""

    model_name: str
    slug: str
    dimensions: int
    registry_size: str
    license: str


MODELS = (
    EmbeddingModel(
        "jinaai/jina-embeddings-v2-base-code",
        "jina-embeddings-v2-base-code",
        768,
        "0.64 GB",
        "Apache-2.0",
    ),
    EmbeddingModel(
        "BAAI/bge-small-en-v1.5",
        "bge-small-en-v1.5",
        384,
        "0.067 GB",
        "MIT",
    ),
)
CONTROL_MODEL = "models/gemini-embedding-001"
CONTROL_DIMENSIONS = 768


def text_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def cache_path(
    cache_root: Path,
    model: EmbeddingModel,
    role: VectorRole,
    value: str,
) -> Path:
    """Return a versioned cache path without storing the source text."""

    digest = text_hash(value)
    return (
        cache_root
        / model.slug
        / f"fastembed-{FASTEMBED_VERSION}-dimensions-{model.dimensions}"
        / role
        / f"{digest}.json"
    )


def cache_record(
    model: EmbeddingModel,
    role: VectorRole,
    value: str,
    vector: Sequence[float],
) -> dict[str, Any]:
    checked = validate_vector(vector, model.dimensions)
    return {
        "experiment_version": EXPERIMENT_VERSION,
        "embedding_model": model.model_name,
        "dimensions": model.dimensions,
        "library": "fastembed",
        "library_version": FASTEMBED_VERSION,
        "role": role,
        "text_sha256": text_hash(value),
        "vector": checked,
    }


def validate_vector(vector: Sequence[object], dimensions: int) -> list[float]:
    if len(vector) != dimensions or any(
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        for value in vector
    ):
        raise ValueError("Embedding cache vector has invalid dimensions or values")
    return [float(value) for value in vector]


def read_cache_record(
    value: Mapping[str, Any],
    model: EmbeddingModel,
    role: VectorRole,
    source_text: str,
) -> list[float]:
    expected = {
        "experiment_version": EXPERIMENT_VERSION,
        "embedding_model": model.model_name,
        "dimensions": model.dimensions,
        "library": "fastembed",
        "library_version": FASTEMBED_VERSION,
        "role": role,
        "text_sha256": text_hash(source_text),
    }
    if any(value.get(key) != expected_value for key, expected_value in expected.items()):
        raise ValueError("Embedding cache identity does not match the requested input")
    vector = value.get("vector")
    if not isinstance(vector, list):
        raise ValueError("Embedding cache record has no vector")
    return validate_vector(vector, model.dimensions)


def require_development_records(
    records: Sequence[Mapping[str, Any]],
    allowed_ids: set[str],
    split: str,
) -> list[dict[str, Any]]:
    """Reject any caller data that is not exactly the selected development set."""

    if split != "development":
        raise ValueError("Local embedding comparison accepts development data only")
    record_ids = [record.get("id") for record in records]
    if (
        any(not isinstance(record_id, str) or not record_id for record_id in record_ids)
        or len(record_ids) != len(set(record_ids))
        or set(record_ids) != allowed_ids
    ):
        raise ValueError("Question records must exactly match the development split")
    return [dict(record) for record in records]


def cosine_distance(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        raise ValueError("Cosine vectors must have equal, non-zero dimensions")
    left_norm = math.sqrt(math.fsum(value * value for value in left))
    right_norm = math.sqrt(math.fsum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Cosine vectors must have non-zero norms")
    similarity = math.fsum(a * b for a, b in zip(left, right)) / (
        left_norm * right_norm
    )
    return 1.0 - max(-1.0, min(1.0, similarity))


def rank_vectors(
    chunks: Sequence[Mapping[str, Any]],
    document_vectors: Mapping[str, Sequence[float]],
    query_vector: Sequence[float],
    *,
    limit: int = TOP_K,
) -> list[dict[str, Any]]:
    """Rank vectors in memory with the production vector-branch tie keys."""

    if limit <= 0:
        return []
    ranked: list[dict[str, Any]] = []
    for chunk in chunks:
        vector = document_vectors[str(chunk["content"])]
        ranked.append(
            {
                **chunk,
                "distance": cosine_distance(vector, query_vector),
            }
        )
    ranked.sort(
        key=lambda row: (
            float(row["distance"]),
            str(row["file_path"]),
            int(row["line_start"])
            if isinstance(row.get("line_start"), int)
            else math.inf,
            int(row["line_end"])
            if isinstance(row.get("line_end"), int)
            else math.inf,
        )
    )
    return ranked[:limit]


def fuse_rankings(
    repository_id: int,
    vector_results: Sequence[Mapping[str, Any]],
    fulltext_results: Sequence[Mapping[str, Any]],
    *,
    limit: int = TOP_K,
) -> list[dict[str, Any]]:
    """Apply production RRF and deterministic hybrid tie ordering."""

    vector_ranks = {
        row["id"]: index + 1 for index, row in enumerate(vector_results)
    }
    fulltext_ranks = {
        row["id"]: index + 1 for index, row in enumerate(fulltext_results)
    }
    vector_by_id = {row["id"]: row for row in vector_results}
    fulltext_by_id = {row["id"]: row for row in fulltext_results}
    candidate_ids = list(vector_ranks)
    candidate_ids.extend(
        chunk_id for chunk_id in fulltext_ranks if chunk_id not in vector_ranks
    )
    fused: list[dict[str, Any]] = []
    for chunk_id in candidate_ids:
        vector = vector_by_id.get(chunk_id, {})
        fulltext = fulltext_by_id.get(chunk_id, {})
        vector_rank = vector_ranks.get(chunk_id)
        fulltext_rank = fulltext_ranks.get(chunk_id)
        fused.append(
            {
                "id": chunk_id,
                "repository_id": repository_id,
                "file_path": vector.get("file_path") or fulltext.get("file_path"),
                "line_start": vector.get("line_start") or fulltext.get("line_start"),
                "line_end": vector.get("line_end") or fulltext.get("line_end"),
                "content": vector.get("content") or fulltext.get("content"),
                "vector_score": vector.get("distance"),
                "fts_score": fulltext.get("score"),
                "rrf_score": (
                    (1 / (RRF_CONSTANT + vector_rank) if vector_rank else 0.0)
                    + (1 / (RRF_CONSTANT + fulltext_rank) if fulltext_rank else 0.0)
                ),
            }
        )
    fused.sort(
        key=lambda row: (
            -float(row["rrf_score"]),
            vector_ranks.get(row["id"], math.inf),
            fulltext_ranks.get(row["id"], math.inf),
            str(row.get("file_path") or ""),
            int(row["line_start"])
            if isinstance(row.get("line_start"), int)
            else math.inf,
            int(row["line_end"])
            if isinstance(row.get("line_end"), int)
            else math.inf,
        )
    )
    return fused[:limit]


def label_rank(
    results: Sequence[Mapping[str, Any]],
    question: Mapping[str, Any],
) -> int | None:
    labels = question.get("relevant", [])
    if not isinstance(labels, list):
        raise ValueError("Development question labels must be a list")
    return first_relevant_rank(results, labels)


def paired_bootstrap(
    control_ranks: Sequence[int | None],
    candidate_ranks: Sequence[int | None],
) -> dict[str, float | int]:
    if len(control_ranks) != len(candidate_ranks) or not control_ranks:
        raise ValueError("Paired rank lists must be non-empty and equal length")
    differences = [
        _reciprocal_rank(candidate) - _reciprocal_rank(control)
        for control, candidate in zip(control_ranks, candidate_ranks)
    ]
    rng = random.Random(BOOTSTRAP_SEED)
    sampled_means = [
        sum(rng.choice(differences) for _ in differences) / len(differences)
        for _ in range(BOOTSTRAP_RESAMPLES)
    ]
    sampled_means.sort()
    alpha = (1 - BOOTSTRAP_INTERVAL) / 2
    return {
        "seed": BOOTSTRAP_SEED,
        "resamples": BOOTSTRAP_RESAMPLES,
        "mean_difference": sum(differences) / len(differences),
        "lower": _linear_percentile(sampled_means, alpha),
        "upper": _linear_percentile(sampled_means, 1 - alpha),
        "sign_test_p_value": exact_sign_test(
            sum(value > 0 for value in differences),
            sum(value < 0 for value in differences),
        ),
    }


def summarize_ranks(ranks: Sequence[int | None]) -> dict[str, Any]:
    if not ranks:
        raise ValueError("Cannot summarize an empty rank sequence")
    return {
        "question_count": len(ranks),
        "mrr": sum(_reciprocal_rank(rank) for rank in ranks) / len(ranks),
        **{
            f"hit_at_{k}": sum(rank is not None and rank <= k for rank in ranks)
            for k in (1, 3, 5)
        },
    }


def summarize_distances(values: Sequence[float]) -> dict[str, float | int | None]:
    if not values:
        return {"count": 0, "minimum": None, "median": None, "maximum": None}
    return {
        "count": len(values),
        "minimum": min(values),
        "median": median(values),
        "maximum": max(values),
    }


def retention_rules(
    control_by_repository: Mapping[str, Mapping[str, Any]],
    candidate_by_repository: Mapping[str, Mapping[str, Any]],
    control_ranks: Sequence[int | None],
    candidate_ranks: Sequence[int | None],
    bootstrap: Mapping[str, Any],
    control_unanswerable_guard: Mapping[str, Sequence[bool]],
    candidate_unanswerable_guard: Mapping[str, Sequence[bool]],
) -> dict[str, Any]:
    if not control_ranks or len(control_ranks) != len(candidate_ranks):
        raise ValueError("Retention requires paired answerable question ranks")
    control_mrr = summarize_ranks(control_ranks)["mrr"]
    candidate_mrr = summarize_ranks(candidate_ranks)["mrr"]
    r4_by_repository: dict[str, bool] = {}
    for repository, control_decisions in control_unanswerable_guard.items():
        candidate_decisions = candidate_unanswerable_guard.get(repository)
        if candidate_decisions is None or len(control_decisions) != len(candidate_decisions):
            raise ValueError("R4 requires paired guard decisions for every repository")
        r4_by_repository[repository] = all(
            not candidate_accept or control_accept
            for control_accept, candidate_accept in zip(
                control_decisions,
                candidate_decisions,
            )
        )
    rules = {
        "R1": candidate_mrr - control_mrr >= 0.03,
        "R2": float(bootstrap["lower"]) > 0,
        "R3": all(
            candidate_by_repository[repository]["hit_at_5"]
            >= control_by_repository[repository]["hit_at_5"]
            for repository in control_by_repository
        ),
        "R4": all(r4_by_repository.values()),
    }
    if all(rules.values()):
        outcome = (
            "candidate: needs a separately registered held-out validation, "
            "a per-model guard threshold under item 3b, and a production migration "
            "plan before any adoption"
        )
    elif all(rules[key] for key in ("R1", "R2", "R3")) and not rules["R4"]:
        outcome = "retrieval-promising; guard needs per-model recalibration; control kept"
    else:
        outcome = "keep control"
    return {
        "rules": rules,
        "control_mrr": control_mrr,
        "candidate_mrr": candidate_mrr,
        "mrr_delta": candidate_mrr - control_mrr,
        "outcome": outcome,
    }


def _reciprocal_rank(rank: int | None) -> float:
    return 1 / rank if rank is not None else 0.0


def _linear_percentile(sorted_values: Sequence[float], quantile: float) -> float:
    position = (len(sorted_values) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] + fraction * (
        sorted_values[upper] - sorted_values[lower]
    )
