"""Evidence quality guard for grounded investigation results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

# Reporting threshold only. The evaluation harness still uses it for diagnostics, but it is NOT
# part of the sufficiency decision (checklist item 3a): every non-empty fused result scores at
# least 1/61 = 0.016393, so the old check could never fail.
MIN_ACCEPTABLE_RRF_SCORE = 0.016
# Provisional cutoff, kept unchanged until it is re-validated on the held-out split (item 3b).
MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5


def _vector_distance(result: Mapping[str, object]) -> float | None:
    score = result.get("vector_score")
    return float(score) if isinstance(score, (int, float)) else None


def evaluate_evidence_sufficiency(
    retrieval_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Decide whether retrieved evidence is sufficient.

    A chunk qualifies on its own vector distance. RRF is used for ranking only, and a chunk with
    no vector distance (for example a full-text-only hit) cannot make evidence sufficient.
    """

    mapping_results = [result for result in retrieval_results if isinstance(result, Mapping)]
    if not mapping_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    best_rrf_score = max(float(result.get("rrf_score", 0.0)) for result in mapping_results)
    distances = [
        distance for result in mapping_results if (distance := _vector_distance(result)) is not None
    ]
    best_vector_score = min(distances) if distances else None

    if best_vector_score is None:
        is_sufficient = False
        reason = "No vector similarity score was retrieved."
    elif best_vector_score <= MAX_ACCEPTABLE_VECTOR_DISTANCE:
        is_sufficient = True
        reason = "At least one retrieved chunk is within the maximum vector distance."
    else:
        is_sufficient = False
        reason = "Best vector cosine distance is above the maximum threshold."

    return {
        "is_sufficient": is_sufficient,
        "reason": reason,
        "best_rrf_score": best_rrf_score,
        "best_vector_score": best_vector_score,
    }
