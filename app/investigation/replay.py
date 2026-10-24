"""Replay metadata for persisted investigation audits."""

from __future__ import annotations

import hashlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass


@dataclass(frozen=True)
class ReplayRecord:
    """Optional request and execution details sufficient to inspect an investigation."""

    prompt: str | None = None
    prompt_version: str | None = None
    raw_response: str | None = None
    raw_self_rating: str | None = None
    generation_params: dict[str, object] | None = None
    thresholds: dict[str, object] | None = None
    embedding_model: str | None = None
    chunk_records: list[dict[str, object]] | None = None
    trace: dict[str, object] | None = None


def build_chunk_records(
    all_results: Sequence[Mapping[str, object]],
    kept_ids: Sequence[object],
) -> list[dict[str, object]]:
    """Describe each ranked result and whether it was included in the prompt."""

    kept_chunk_ids = {str(chunk_id) for chunk_id in kept_ids}
    return [
        {
            "chunk_id": str(result.get("id")),
            "rank": rank,
            "content_hash": hashlib.sha256(
                str(result.get("content") or "").encode("utf-8")
            ).hexdigest(),
            "file_path": result.get("file_path"),
            "line_start": result.get("line_start"),
            "line_end": result.get("line_end"),
            "vector_score": result.get("vector_score"),
            "fts_score": result.get("fts_score"),
            "rrf_score": result.get("rrf_score"),
            "kept_in_prompt": str(result.get("id")) in kept_chunk_ids,
        }
        for rank, result in enumerate(all_results, start=1)
    ]
