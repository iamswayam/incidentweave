"""Calibrate model confidence against retrieval strength."""

from __future__ import annotations

MIN_CLEAR_RRF_SCORE = 0.032
MAX_CLEAR_VECTOR_DISTANCE = 0.4


def calibrate_confidence(
    reported_confidence: str,
    best_rrf_score: float | None,
    best_vector_score: float | None,
) -> tuple[str, str]:
    """Downgrade a high model rating when accepted evidence is borderline."""

    normalized_confidence = reported_confidence.strip().lower()
    if normalized_confidence != "high":
        return normalized_confidence, "Model confidence retained; calibration only downgrades high."

    weak_rrf = best_rrf_score is not None and best_rrf_score < MIN_CLEAR_RRF_SCORE
    borderline_distance = (
        best_vector_score is not None
        and best_vector_score > MAX_CLEAR_VECTOR_DISTANCE
    )
    if weak_rrf or borderline_distance:
        reasons: list[str] = []
        if weak_rrf:
            reasons.append(
                f"best RRF {best_rrf_score:.6f} is below {MIN_CLEAR_RRF_SCORE:.3f}"
            )
        if borderline_distance:
            reasons.append(
                "best vector distance "
                f"{best_vector_score:.6f} is above {MAX_CLEAR_VECTOR_DISTANCE:.1f}"
            )
        return "medium", "High confidence downgraded: " + "; ".join(reasons) + "."

    return "high", "High confidence retained; retrieval scores clear both calibration margins."
