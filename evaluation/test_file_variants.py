"""Pure implementations of the registered test-file ranking variants."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from evaluation.test_files import is_test_path

TOP_K = 5


def _number_or_infinity(value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return float("inf")
    return float(value)


def _production_order(result: Mapping[str, Any]) -> tuple[float | str, ...]:
    """Keep production's RRF, branch-rank, path, and line tie-break order."""

    return (
        -float(result["rrf_score"]),
        _number_or_infinity(result.get("vector_rank")),
        _number_or_infinity(result.get("fulltext_rank")),
        str(result.get("file_path") or ""),
        _number_or_infinity(result.get("line_start")),
        _number_or_infinity(result.get("line_end")),
    )


def control_top_five(
    full_fused_ranking: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Return production's top five from the full union of branch candidates."""

    return [dict(result) for result in full_fused_ranking[:TOP_K]]


def downweight_test_chunks(
    full_fused_ranking: Sequence[Mapping[str, Any]],
    *,
    factor: float = 0.5,
) -> list[dict[str, Any]]:
    """Downweight test chunks after fusion, then apply production ordering and top-k.

    The full fused candidate union is retained until after the score adjustment so
    non-test candidates can move into the final five without losing branch candidates.
    """

    if not 0 <= factor <= 1:
        raise ValueError("The test-chunk weight must be between zero and one")
    adjusted: list[dict[str, Any]] = []
    for result in full_fused_ranking:
        candidate = dict(result)
        if is_test_path(str(candidate.get("file_path") or "")):
            candidate["rrf_score"] = float(candidate["rrf_score"]) * factor
        adjusted.append(candidate)
    adjusted.sort(key=_production_order)
    return adjusted[:TOP_K]


def exclude_test_chunks(
    full_fused_ranking: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Remove test chunks before the final top-k cut so results refill from candidates."""

    retained = [
        dict(result)
        for result in full_fused_ranking
        if not is_test_path(str(result.get("file_path") or ""))
    ]
    retained.sort(key=_production_order)
    return retained[:TOP_K]
