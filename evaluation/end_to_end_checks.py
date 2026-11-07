"""Pure, deterministic checks for recorded end-to-end investigation runs."""

from __future__ import annotations

import json
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from typing import Any

from app.text import normalize_whitespace
from evaluation.stats import wilson_interval

ANSWERED = "answered"
REFUSED_OUTCOMES = frozenset({"refused_guard", "abstained_model"})
DEGRADED_OUTCOMES = frozenset({"generation_unavailable", "embedding_unavailable"})
RUN_REPEAT_INDICES = frozenset({1, 2, 3})


@dataclass(frozen=True)
class Citation:
    """One submitted citation, retaining malformed values as invalid evidence."""

    chunk_id: str | None
    quote: str | None


@dataclass(frozen=True)
class RecordedRun:
    """Minimal run data required by citation, outcome, and stability checks."""

    question_id: str
    answerable: bool
    outcome: str
    citations: tuple[Citation, ...]
    retrieved_chunk_ids: frozenset[str]
    retrieved_chunk_texts: Mapping[str, str]
    repeat_index: int
    error_classes: tuple[str, ...] = ()
    retry_used: bool | None = None


def _citations_from_response(raw_response: object) -> tuple[Citation, ...]:
    if not isinstance(raw_response, str) or not raw_response:
        return ()
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise ValueError("recorded raw response is not valid JSON") from exc
    if not isinstance(payload, Mapping):
        raise ValueError("recorded raw response must be a JSON object")
    claims = payload.get("claims")
    if not isinstance(claims, list):
        return ()

    citations: list[Citation] = []
    for claim in claims:
        if not isinstance(claim, Mapping):
            continue
        claim_text = claim.get("text")
        if not isinstance(claim_text, str) or not claim_text.strip():
            continue
        evidence = claim.get("evidence")
        if not isinstance(evidence, list):
            continue
        for item in evidence:
            if not isinstance(item, Mapping):
                citations.append(Citation(chunk_id=None, quote=None))
                continue
            chunk_id = item.get("chunk_id")
            quote = item.get("quote")
            citations.append(
                Citation(
                    chunk_id=chunk_id if isinstance(chunk_id, str) else None,
                    quote=quote if isinstance(quote, str) else None,
                )
            )
    return tuple(citations)


def recorded_run_from_replay(
    audit_record: Mapping[str, Any],
    *,
    question_id: str,
    answerable: bool,
    repeat_index: int,
    retrieved_chunk_texts: Mapping[str, str],
) -> RecordedRun:
    """Convert persisted replay/audit data, supplying chunk text stored elsewhere."""

    trace = audit_record.get("trace")
    trace = trace if isinstance(trace, Mapping) else {}
    outcome = trace.get("outcome", audit_record.get("outcome"))
    if not isinstance(outcome, str) or not outcome:
        raise ValueError("persisted audit record has no outcome")

    raw_response = audit_record.get("raw_response")
    if raw_response is None and outcome in {ANSWERED, "abstained_model"}:
        raise ValueError("persisted answer is missing its raw response")
    citations = _citations_from_response(raw_response)
    chunk_records = audit_record.get("chunk_records")
    if not isinstance(chunk_records, list):
        chunk_records = []
    retrieved_ids = frozenset(
        str(item["chunk_id"])
        for item in chunk_records
        if isinstance(item, Mapping)
        and item.get("kept_in_prompt") is True
        and item.get("chunk_id") is not None
    )
    return RecordedRun(
        question_id=question_id,
        answerable=answerable,
        outcome=outcome,
        citations=citations,
        retrieved_chunk_ids=retrieved_ids,
        retrieved_chunk_texts={
            chunk_id: text
            for chunk_id, text in retrieved_chunk_texts.items()
            if chunk_id in retrieved_ids
        },
        repeat_index=repeat_index,
        error_classes=tuple(
            error
            for error in (
                trace.get("error_classes", [])
                if isinstance(trace.get("error_classes"), list)
                else []
            )
            if isinstance(error, str)
        ),
        retry_used=trace.get("retry_used") if isinstance(trace.get("retry_used"), bool) else None,
    )


def recorded_run_from_service_result(
    question_id: str,
    answerable: bool,
    repeat_index: int,
    result: Mapping[str, Any],
) -> RecordedRun:
    """Convert the service response, preserving submitted citations and retrieved text."""

    outcome = result.get("outcome")
    if not isinstance(outcome, str) or not outcome:
        raise ValueError("investigation service result has no outcome")
    generation_trace = result.get("generation_trace")
    raw_response = (
        generation_trace.get("raw_text") if isinstance(generation_trace, Mapping) else None
    )
    if raw_response is None and outcome in {ANSWERED, "abstained_model"}:
        raise ValueError("investigation answer is missing its raw response")
    retrieved_results = result.get("retrieval_results")
    if not isinstance(retrieved_results, list):
        retrieved_results = []
    retrieved_ids: set[str] = set()
    retrieved_texts: dict[str, str] = {}
    for item in retrieved_results:
        if not isinstance(item, Mapping) or item.get("id") is None:
            continue
        chunk_id = str(item["id"])
        content = item.get("content")
        if not isinstance(content, str):
            raise ValueError(f"retrieved chunk {chunk_id!r} has no text")
        retrieved_ids.add(chunk_id)
        retrieved_texts[chunk_id] = content
    return RecordedRun(
        question_id=question_id,
        answerable=answerable,
        outcome=outcome,
        citations=_citations_from_response(raw_response),
        retrieved_chunk_ids=frozenset(retrieved_ids),
        retrieved_chunk_texts=retrieved_texts,
        repeat_index=repeat_index,
        error_classes=tuple(
            error
            for error in (
                generation_trace.get("error_classes", [])
                if isinstance(generation_trace, Mapping)
                and isinstance(generation_trace.get("error_classes"), list)
                else []
            )
            if isinstance(error, str)
        ),
        retry_used=result.get("retry_used") if isinstance(result.get("retry_used"), bool) else None,
    )


def _proportion(successes: int, denominator: int) -> dict[str, Any]:
    if denominator == 0:
        return {
            "successes": successes,
            "denominator": 0,
            "rate": None,
            "wilson_95": None,
        }
    low, high = wilson_interval(successes, denominator)
    return {
        "successes": successes,
        "denominator": denominator,
        "rate": successes / denominator,
        "wilson_95": [low, high],
    }


def _citation_checks(records: Sequence[RecordedRun]) -> dict[str, Any]:
    submitted = [citation for record in records for citation in record.citations]
    valid = 0
    grounded = 0
    for record in records:
        for citation in record.citations:
            if citation.chunk_id in record.retrieved_chunk_ids:
                grounded += 1
            if citation.chunk_id is None or citation.quote is None:
                continue
            chunk = record.retrieved_chunk_texts.get(citation.chunk_id)
            if chunk is None:
                continue
            quote = normalize_whitespace(citation.quote)
            if len(quote) >= 10 and quote in normalize_whitespace(chunk):
                valid += 1
    answered = [record for record in records if record.outcome == ANSWERED]
    answered_with_citations = sum(bool(record.citations) for record in answered)
    return {
        "submitted_citations": len(submitted),
        "valid_citations": valid,
        "citation_quote_validity": _proportion(valid, len(submitted)),
        "retrieved_citations": grounded,
        "retrieval_grounded_citation_rate": _proportion(grounded, len(submitted)),
        "answered_with_citations": _proportion(answered_with_citations, len(answered)),
    }


def _outcome_checks(records: Sequence[RecordedRun]) -> dict[str, Any]:
    degraded_counts = {
        outcome: sum(record.outcome == outcome for record in records)
        for outcome in sorted(DEGRADED_OUTCOMES)
    }
    usable = [record for record in records if record.outcome not in DEGRADED_OUTCOMES]
    unanswerable = [record for record in usable if not record.answerable]
    answerable = [record for record in usable if record.answerable]
    false_answers = sum(record.outcome == ANSWERED for record in unanswerable)
    false_refusals = sum(record.outcome in REFUSED_OUTCOMES for record in answerable)
    correct = sum(
        record.outcome == ANSWERED if record.answerable else record.outcome in REFUSED_OUTCOMES
        for record in usable
    )
    outcome_counts: dict[str, int] = {}
    error_class_counts: dict[str, int] = {}
    for record in records:
        outcome_counts[record.outcome] = outcome_counts.get(record.outcome, 0) + 1
        for error_class in record.error_classes:
            error_class_counts[error_class] = error_class_counts.get(error_class, 0) + 1
    return {
        "non_degraded_record_count": len(usable),
        "degraded_outcome_counts": degraded_counts,
        "provider_error_count": outcome_counts.get("error", 0),
        "provider_error_class_counts": dict(sorted(error_class_counts.items())),
        "outcome_counts": dict(sorted(outcome_counts.items())),
        "false_answer_rate": _proportion(false_answers, len(unanswerable)),
        "false_refusal_rate": _proportion(false_refusals, len(answerable)),
        "overall_correctness": _proportion(correct, len(usable)),
    }


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    return 1.0 if not union else len(left & right) / len(union)


def _stability_checks(records: Sequence[RecordedRun]) -> dict[str, Any]:
    grouped: dict[str, list[RecordedRun]] = defaultdict(list)
    for record in records:
        if record.repeat_index not in RUN_REPEAT_INDICES:
            raise ValueError("repeat_index must be 1, 2, or 3")
        grouped[record.question_id].append(record)

    complete: list[list[RecordedRun]] = []
    incomplete_ids: list[str] = []
    for question_id in sorted(grouped):
        runs = grouped[question_id]
        indices = [record.repeat_index for record in runs]
        if len(indices) != len(set(indices)):
            raise ValueError(f"{question_id}: duplicate repeat_index")
        if len(runs) != 3 or set(indices) != RUN_REPEAT_INDICES:
            incomplete_ids.append(question_id)
            continue
        if len({record.answerable for record in runs}) != 1:
            raise ValueError(f"{question_id}: answerability differs across runs")
        complete.append(sorted(runs, key=lambda record: record.repeat_index))

    stable_count = 0
    flip_count = 0
    jaccard_values: list[float] = []
    pair_indices = ((0, 1), (0, 2), (1, 2))
    for runs in complete:
        outcomes = {record.outcome for record in runs}
        stable_count += len(outcomes) == 1
        has_answered = any(record.outcome == ANSWERED for record in runs)
        has_refused = any(record.outcome in REFUSED_OUTCOMES for record in runs)
        flip_count += has_answered and has_refused
        citation_sets = [
            frozenset(
                citation.chunk_id for citation in record.citations if citation.chunk_id is not None
            )
            for record in runs
        ]
        if sum(bool(citation_set) for citation_set in citation_sets) >= 2:
            jaccard_values.append(
                sum(
                    _jaccard(citation_sets[left], citation_sets[right])
                    for left, right in pair_indices
                )
                / len(pair_indices)
            )

    return {
        "question_set_count": len(grouped),
        "complete_question_set_count": len(complete),
        "incomplete_question_set_count": len(incomplete_ids),
        "incomplete_question_ids": incomplete_ids,
        "stable_outcome_questions": _proportion(stable_count, len(complete)),
        "mean_cited_chunk_jaccard": (
            {
                "mean": sum(jaccard_values) / len(jaccard_values),
                "question_count": len(jaccard_values),
            }
            if jaccard_values
            else {"mean": None, "question_count": 0}
        ),
        "flip_questions": {"count": flip_count, "denominator": len(complete)},
    }


def summarize_end_to_end(records: Sequence[RecordedRun]) -> dict[str, Any]:
    """Compute all registered metrics with explicit numerators and denominators."""

    citations = _citation_checks(records)
    return {
        "record_count": len(records),
        "question_count": len({record.question_id for record in records}),
        "check_a": citations,
        "check_b": {
            "retrieved_citations": citations["retrieved_citations"],
            "submitted_citations": citations["submitted_citations"],
            "retrieval_grounded_citation_rate": citations["retrieval_grounded_citation_rate"],
        },
        "check_c": _outcome_checks(records),
        "check_d": _stability_checks(records),
        "run_diagnostics": {
            "retried_run_count": sum(record.retry_used is True for record in records),
            "retry_status_unknown_count": sum(record.retry_used is None for record in records),
        },
    }


def format_end_to_end_markdown(
    summary: Mapping[str, Any],
    *,
    generated_at: str | None = None,
    skipped_questions: Sequence[Mapping[str, str]] = (),
) -> str:
    """Render a deterministic report for the registered item 34 metrics."""

    def rate(value: Mapping[str, Any]) -> str:
        result = value["rate"]
        if result is None:
            return f"undefined (0/{value['denominator']})"
        return f"{result:.3f} ({value['successes']}/{value['denominator']})"

    def rate_with_interval(value: Mapping[str, Any]) -> str:
        text = rate(value)
        interval = value["wilson_95"]
        return (
            f"{text}; Wilson 95% [{interval[0]:.3f}, {interval[1]:.3f}]"
            if interval is not None
            else f"{text}; Wilson 95% undefined"
        )

    a = summary["check_a"]
    b = summary["check_b"]
    c = summary["check_c"]
    d = summary["check_d"]
    jaccard = d["mean_cited_chunk_jaccard"]
    jaccard_text = "undefined" if jaccard["mean"] is None else f"{jaccard['mean']:.3f}"
    error_classes = ", ".join(
        f"{name}={count}" for name, count in c["provider_error_class_counts"].items()
    )
    lines = [
        "# End-to-end citation and stability checks",
        "",
    ]
    if generated_at is not None:
        lines.extend([f"Generated at: {generated_at}", ""])
    lines.extend(
        [
            f"Recorded runs: {summary['record_count']}; questions: {summary['question_count']}.",
            "",
            "## Check A — quote in cited chunk",
            "",
            f"- Citation quote validity: {rate(a['citation_quote_validity'])}.",
            f"- Answered investigations with at least one citation: "
            f"{rate(a['answered_with_citations'])}.",
            "",
            "## Check B — cited chunk in retrieved set",
            "",
            f"- Retrieval-grounded citation rate: {rate(b['retrieval_grounded_citation_rate'])}.",
            "",
            "## Check C — refusal correctness",
            "",
            f"- False-answer rate: {rate_with_interval(c['false_answer_rate'])}.",
            f"- False-refusal rate: {rate_with_interval(c['false_refusal_rate'])}.",
            f"- Overall correctness: {rate_with_interval(c['overall_correctness'])}.",
            f"- Degraded outcomes: generation_unavailable="
            f"{c['degraded_outcome_counts']['generation_unavailable']}, "
            f"embedding_unavailable={c['degraded_outcome_counts']['embedding_unavailable']}.",
            f"- Provider error outcomes: {c['provider_error_count']}; "
            f"non-degraded correctness denominator: {c['non_degraded_record_count']}.",
            f"- Provider error classes: {error_classes or 'none'}.",
            "",
            "## Check D — stability",
            "",
            f"- Stable outcomes: {rate(d['stable_outcome_questions'])}; "
            f"complete question sets: {d['complete_question_set_count']}.",
            f"- Mean cited-chunk-set pairwise Jaccard: "
            f"{jaccard_text} (questions={jaccard['question_count']}).",
            f"- Answered/refused flips: {d['flip_questions']['count']}/"
            f"{d['flip_questions']['denominator']}.",
            f"- Incomplete question sets: {d['incomplete_question_set_count']}.",
            f"- Incomplete question IDs: {', '.join(d['incomplete_question_ids']) or 'none'}.",
            f"- Runs with retries: {summary['run_diagnostics']['retried_run_count']}; "
            f"retry status unknown: {summary['run_diagnostics']['retry_status_unknown_count']}.",
            "",
            f"Skipped questions: {len(skipped_questions)}.",
        ]
    )
    lines.extend(
        f"- {item.get('question_id', '')} ({item.get('source_file', '')}): {item.get('reason', '')}"
        for item in skipped_questions
    )
    return "\n".join(lines)


def recorded_run_to_dict(record: RecordedRun) -> dict[str, Any]:
    """Return a stable JSON-compatible representation of one run."""

    result = asdict(record)
    result["retrieved_chunk_ids"] = sorted(record.retrieved_chunk_ids)
    result["retrieved_chunk_texts"] = dict(sorted(record.retrieved_chunk_texts.items()))
    result["error_classes"] = list(record.error_classes)
    return result


def recorded_run_from_dict(data: Mapping[str, Any]) -> RecordedRun:
    """Validate and decode one JSON-compatible run record."""

    question_id = data.get("question_id")
    answerable = data.get("answerable")
    outcome = data.get("outcome")
    repeat_index = data.get("repeat_index")
    citations_data = data.get("citations")
    retrieved_ids = data.get("retrieved_chunk_ids")
    retrieved_texts = data.get("retrieved_chunk_texts")
    error_classes = data.get("error_classes", [])
    retry_used = data.get("retry_used")
    if not isinstance(question_id, str) or not isinstance(outcome, str):
        raise ValueError("run record requires string question_id and outcome")
    if not isinstance(answerable, bool) or not isinstance(repeat_index, int):
        raise ValueError("run record requires boolean answerable and integer repeat_index")
    if not isinstance(citations_data, list) or not isinstance(retrieved_ids, list):
        raise ValueError("run record citations and retrieved_chunk_ids must be lists")
    if not isinstance(retrieved_texts, Mapping) or not isinstance(error_classes, list):
        raise ValueError("run record retrieved_chunk_texts and error_classes have invalid types")
    citations = []
    for item in citations_data:
        if not isinstance(item, Mapping):
            raise ValueError("run record citation must be an object")
        chunk_id = item.get("chunk_id")
        quote = item.get("quote")
        citations.append(
            Citation(
                chunk_id=chunk_id if isinstance(chunk_id, str) else None,
                quote=quote if isinstance(quote, str) else None,
            )
        )
    if any(not isinstance(item, str) for item in retrieved_ids):
        raise ValueError("run record retrieved chunk IDs must be strings")
    if any(
        not isinstance(key, str) or not isinstance(value, str)
        for key, value in retrieved_texts.items()
    ):
        raise ValueError("run record retrieved chunk text map must contain strings")
    if any(not isinstance(item, str) for item in error_classes):
        raise ValueError("run record error classes must be strings")
    if retry_used is not None and not isinstance(retry_used, bool):
        raise ValueError("run record retry_used must be boolean or null")
    return RecordedRun(
        question_id=question_id,
        answerable=answerable,
        outcome=outcome,
        citations=tuple(citations),
        retrieved_chunk_ids=frozenset(retrieved_ids),
        retrieved_chunk_texts=dict(retrieved_texts),
        repeat_index=repeat_index,
        error_classes=tuple(error_classes),
        retry_used=retry_used,
    )
