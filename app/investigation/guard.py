"""Evidence quality guard for grounded investigation results."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

MIN_ACCEPTABLE_RRF_SCORE = 0.016
MAX_ACCEPTABLE_VECTOR_DISTANCE = 0.5


def evaluate_evidence_sufficiency(
    retrieval_results: Sequence[Mapping[str, object]],
) -> dict[str, object]:
    """Return whether the retrieved evidence is strong enough for a Gemini call."""

    if not retrieval_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    mapping_results = [result for result in retrieval_results if isinstance(result, Mapping)]
    if not mapping_results:
        return {
            "is_sufficient": False,
            "reason": "No repository evidence was retrieved.",
            "best_rrf_score": None,
            "best_vector_score": None,
        }

    best_rrf_score = max(float(result.get("rrf_score", 0.0)) for result in mapping_results)
    vector_scores = [
        float(score)
        for result in mapping_results
        if isinstance((score := result.get("vector_score")), (int, float))
    ]
    best_vector_score = min(vector_scores) if vector_scores else None

    is_sufficient = (
        best_rrf_score >= MIN_ACCEPTABLE_RRF_SCORE
        and best_vector_score is not None
        and best_vector_score <= MAX_ACCEPTABLE_VECTOR_DISTANCE
    )
    if best_rrf_score < MIN_ACCEPTABLE_RRF_SCORE:
        reason = "Best retrieved evidence score is below the minimum threshold."
    elif best_vector_score is None:
        reason = "No vector similarity score was retrieved."
    elif best_vector_score > MAX_ACCEPTABLE_VECTOR_DISTANCE:
        reason = "Best vector cosine distance is above the maximum threshold."
    else:
        reason = "Evidence strength meets the RRF and vector-distance requirements."

    return {
        "is_sufficient": is_sufficient,
        "reason": reason,
        "best_rrf_score": best_rrf_score,
        "best_vector_score": best_vector_score,
    }
