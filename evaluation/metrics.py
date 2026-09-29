"""Pure, deterministic metrics for Phase 8 evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from statistics import median


def is_relevant(
    result: Mapping[str, object],
    labels: Sequence[Mapping[str, str]],
) -> bool:
    """Return whether a result matches any file/content relevance label."""

    file_path = str(result.get("file_path") or "")
    content = str(result.get("content") or "").casefold()
    return any(
        file_path == str(label["file_path"])
        and str(label["substring"]).casefold() in content
        for label in labels
    )


def first_relevant_rank(
    results: Sequence[Mapping[str, object]],
    labels: Sequence[Mapping[str, str]],
) -> int | None:
    """Return the one-based first relevant rank, or None for no hit."""

    for rank, result in enumerate(results, start=1):
        if is_relevant(result, labels):
            return rank
    return None


def hit_at_k(
    question_results: Sequence[Sequence[Mapping[str, object]]],
    labels_by_question: Sequence[Sequence[Mapping[str, str]]],
    k: int,
) -> int:
    """Count questions with a relevant result in the first k results."""

    return sum(
        first_relevant_rank(results[:k], labels) is not None
        for results, labels in zip(question_results, labels_by_question)
    )


def mean_reciprocal_rank(
    question_results: Sequence[Sequence[Mapping[str, object]]],
    labels_by_question: Sequence[Sequence[Mapping[str, str]]],
) -> float:
    """Return the mean reciprocal rank, counting no-hit questions as zero."""

    if not question_results:
        return 0.0
    reciprocal_ranks = []
    for results, labels in zip(question_results, labels_by_question):
        rank = first_relevant_rank(results, labels)
        reciprocal_ranks.append(1 / rank if rank is not None else 0.0)
    return sum(reciprocal_ranks) / len(reciprocal_ranks)


def retrieval_summary(
    question_results: Sequence[Sequence[Mapping[str, object]]],
    labels_by_question: Sequence[Sequence[Mapping[str, str]]],
) -> dict[str, float | int]:
    """Return hit@1/3/5 and MRR for one retrieval method."""

    return {
        "hit_at_1": hit_at_k(question_results, labels_by_question, 1),
        "hit_at_3": hit_at_k(question_results, labels_by_question, 3),
        "hit_at_5": hit_at_k(question_results, labels_by_question, 5),
        "mrr": mean_reciprocal_rank(question_results, labels_by_question),
    }


def guard_confusion(
    answerable: Sequence[bool],
    sufficient: Sequence[bool],
) -> dict[str, int]:
    """Count guard true/false accepts and refusals against answerability labels."""

    counts = {
        "true_accept": 0,
        "false_refusal": 0,
        "true_refusal": 0,
        "false_accept": 0,
    }
    for expected_answer, accepted in zip(answerable, sufficient):
        if expected_answer and accepted:
            counts["true_accept"] += 1
        elif expected_answer and not accepted:
            counts["false_refusal"] += 1
        elif not expected_answer and not accepted:
            counts["true_refusal"] += 1
        else:
            counts["false_accept"] += 1
    return counts


def best_score_distribution(
    evidence_checks: Iterable[Mapping[str, object]],
    key: str,
) -> dict[str, float | None]:
    """Return min, median, and max for non-null best scores."""

    values = [float(check[key]) for check in evidence_checks if check.get(key) is not None]
    if not values:
        return {"min": None, "median": None, "max": None}
    return {"min": min(values), "median": median(values), "max": max(values)}


def distance_sweep(
    evidence_checks: Sequence[Mapping[str, object]],
    answerable: Sequence[bool],
    rrf_threshold: float,
) -> list[dict[str, float | int]]:
    """Sweep vector cutoffs without rerunning retrieval or changing guard.py."""

    rows: list[dict[str, float | int]] = []
    for index in range(16):
        cutoff = round(0.30 + index * 0.02, 2)
        false_refusals = 0
        false_accepts = 0
        for check, expected_answer in zip(evidence_checks, answerable):
            best_rrf = check.get("best_rrf_score")
            best_vector = check.get("best_vector_score")
            accepted = (
                best_rrf is not None
                and float(best_rrf) >= rrf_threshold
                and best_vector is not None
                and float(best_vector) <= cutoff
            )
            if expected_answer and not accepted:
                false_refusals += 1
            elif not expected_answer and accepted:
                false_accepts += 1
        rows.append(
            {
                "vector_cutoff": cutoff,
                "false_refusals": false_refusals,
                "false_accepts": false_accepts,
            }
        )
    return rows


def answer_screen(diagnosis: str, must_mention: Sequence[Sequence[str]]) -> bool:
    """Check that every acceptable keyword group has one case-insensitive hit."""

    normalized = diagnosis.casefold()
    return all(any(option.casefold() in normalized for option in group) for group in must_mention)


def is_refused(diagnosis: str, generation_latency_ms: int | None = None) -> bool:
    """Detect a guard refusal, not a generated diagnosis containing the marker."""

    return diagnosis.strip() == "INSUFFICIENT_EVIDENCE" and generation_latency_ms is None
