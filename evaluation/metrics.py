"""Pure, deterministic metrics for Phase 8 evaluation."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from statistics import median_high


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
    return {"min": min(values), "median": median_high(values), "max": max(values)}


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


def citation_summary(records: Sequence[Mapping[str, object]]) -> dict[str, int]:
    """Summarize how often cited chunks were actually relevant for answerable questions."""

    answerable = [
        record
        for record in records
        if isinstance(record, Mapping)
        and not str(record.get("category") or "").startswith("unanswerable")
    ]
    cited_total = sum(len(record.get("cited_chunk_ids", [])) for record in answerable)
    cited_relevant = sum(
        sum(
            1
            for item in record.get("cited_chunk_relevance", [])
            if isinstance(item, Mapping) and item.get("relevant")
        )
        for record in answerable
    )
    answers_with_zero_citations = sum(
        1
        for record in answerable
        if record.get("diagnosis") and not record.get("cited_chunk_ids")
    )
    return {
        "cited_total": cited_total,
        "cited_relevant": cited_relevant,
        "answers_with_zero_citations": answers_with_zero_citations,
    }


def guard_diagnostics(
    evidence_checks: Sequence[Mapping[str, object]],
    rrf_threshold: float,
) -> dict[str, float | int | bool]:
    """Summarize whether the RRF guard can reject nonempty vector results."""

    reasons = [str(check.get("reason") or "").lower() for check in evidence_checks]
    rrf_rank1_floor = 1 / (60 + 1)
    return {
        "rrf_threshold": rrf_threshold,
        "rrf_rank1_floor": rrf_rank1_floor,
        "rrf_gate_can_reject_nonempty_vector_results": (
            rrf_threshold > rrf_rank1_floor
        ),
        "rrf_rejections": sum(
            "rrf" in reason or "minimum threshold" in reason for reason in reasons
        ),
        "vector_rejections": sum(
            "vector" in reason or "distance" in reason for reason in reasons
        ),
        "can_reject": rrf_threshold > rrf_rank1_floor,
    }


def latency_summary(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Summarize wall and generation latency across records where generation ran."""

    generation_records = [
        record for record in records if isinstance(record, Mapping) and record.get("generation_ran")
    ]
    return {
        "wall_ms": value_distribution(
            [
                record.get("wall_ms")
                for record in generation_records
                if record.get("wall_ms") is not None
            ]
        ),
        "generation_ms": value_distribution(
            [
                record.get("generation_ms")
                for record in generation_records
                if record.get("generation_ms") is not None
            ]
        ),
    }


def token_summary(records: Sequence[Mapping[str, object]]) -> dict[str, object]:
    """Summarize total-token usage across records where generation produced usage metadata."""

    totals = [
        int(record.get("generation_trace", {}).get("total_tokens"))
        for record in records
        if isinstance(record, Mapping)
        and isinstance(record.get("generation_trace"), Mapping)
        and record.get("generation_trace", {}).get("total_tokens") is not None
    ]
    return {"total_tokens": value_distribution(totals)}


def abstention_kind(
    diagnosis: str,
    generation_ran: bool,
    raw_text: str | None,
) -> str | None:
    """Classify whether an insufficient-evidence result was explicit or a parse fallback."""

    if not generation_ran:
        return None
    if diagnosis.strip() != "INSUFFICIENT_EVIDENCE":
        return None
    if not raw_text:
        return "parse_fallback"
    if "INSUFFICIENT_EVIDENCE" in raw_text:
        return "explicit"
    return "parse_fallback"


def classify_outcome_v2(
    category: str,
    error: object,
    guard_refused: bool,
    abstained: bool,
    labeled_in_context: bool | None,
    screen_pass: bool | None,
) -> str:
    """Return the additive outcome taxonomy for per-question diagnosis analysis."""

    if error:
        return "error"
    if category.startswith("unanswerable"):
        if guard_refused:
            return "guard_true_refusal"
        if abstained:
            return "model_abstained"
        return "answered_unanswerable"
    if guard_refused:
        return "guard_false_refusal"
    if abstained:
        return "retrieval_miss_abstained" if not labeled_in_context else "model_false_abstention"
    if screen_pass is True:
        return "correct_labeled_context" if labeled_in_context else "correct_unlabeled_context"
    if screen_pass is False:
        return "incomplete_or_wrong"
    return "incomplete_or_wrong"


def value_distribution(values: Sequence[float | int | None]) -> dict[str, float | int | None]:
    """Summarize numeric values while ignoring nulls and preserving None for empty inputs."""

    filtered = [value for value in values if value is not None]
    if not filtered:
        return {"min": None, "median": None, "max": None, "count": 0}
    sorted_values = sorted(filtered, key=float)
    median_value = median_high(sorted_values)
    return {
        "min": sorted_values[0],
        "median": median_value,
        "max": sorted_values[-1],
        "count": len(sorted_values),
    }


def is_refused(diagnosis: str, generation_latency_ms: int | None = None) -> bool:
    """Detect a guard refusal, not a generated diagnosis containing the marker."""

    return diagnosis.strip() == "INSUFFICIENT_EVIDENCE" and generation_latency_ms is None
