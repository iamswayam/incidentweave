"""Pure helpers for the test-file retrieval diagnostic."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from evaluation.metrics import first_relevant_rank, first_relevant_span_rank
from evaluation.test_files import is_test_path


def summarize_fixture_paths(
    chunks: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Summarize tagged chunks and distinct paths requiring manual review."""

    tagged_chunk_count = 0
    tagged_paths: set[str] = set()
    untagged_test_paths: set[str] = set()
    for chunk in chunks:
        path = chunk.get("file_path")
        if not isinstance(path, str) or not path:
            raise ValueError("Every fixture chunk must have a non-empty file_path")
        if is_test_path(path):
            tagged_chunk_count += 1
            tagged_paths.add(path)
        elif "test" in path.casefold():
            untagged_test_paths.add(path)

    total_chunks = len(chunks)
    return {
        "total_chunks": total_chunks,
        "tagged_chunk_count": tagged_chunk_count,
        "tagged_chunk_share": (
            tagged_chunk_count / total_chunks if total_chunks else 0.0
        ),
        "tagged_paths": sorted(tagged_paths),
        "untagged_test_paths": sorted(untagged_test_paths),
    }


def summarize_question_results(
    questions: Sequence[Mapping[str, Any]],
    results_by_question: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Summarize test-source exposure and labeled-span hits in top-five results."""

    question_test_counts: list[int] = []
    tagged_test_results = 0
    result_count = 0
    answerable_test_evidence_count = 0
    answerable_test_evidence_hit_count = 0

    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str) or question_id not in results_by_question:
            raise ValueError("Every selected development question needs retrieval results")
        results = results_by_question[question_id][:5]
        test_count = sum(
            is_test_path(str(result.get("file_path") or "")) for result in results
        )
        question_test_counts.append(test_count)
        tagged_test_results += test_count
        result_count += len(results)

        if question.get("category") not in {"direct", "paraphrased"}:
            continue
        spans = question.get("relevant_spans", [])
        if not isinstance(spans, list):
            raise ValueError("Question relevant_spans must be a list")
        has_test_evidence = any(
            isinstance(span, Mapping)
            and isinstance(span.get("file_path"), str)
            and is_test_path(span["file_path"])
            for span in spans
        )
        if has_test_evidence:
            answerable_test_evidence_count += 1
            if first_relevant_span_rank(results, spans) is not None:
                answerable_test_evidence_hit_count += 1

    return {
        "development_question_count": len(questions),
        "question_top5_test_counts": question_test_counts,
        "top5_test_chunk_count": tagged_test_results,
        "top5_result_count": result_count,
        "top5_test_share": (
            tagged_test_results / result_count if result_count else 0.0
        ),
        "answerable_test_evidence_question_count": answerable_test_evidence_count,
        "answerable_test_evidence_hit_at_5": answerable_test_evidence_hit_count,
    }


def build_repository_diagnostic(
    chunks: Sequence[Mapping[str, Any]],
    questions: Sequence[Mapping[str, Any]],
    results_by_question: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Combine fixture path and development retrieval summaries for one repository."""

    return {
        **summarize_fixture_paths(chunks),
        **summarize_question_results(questions, results_by_question),
    }


def reconcile_control(
    questions: Sequence[Mapping[str, Any]],
    diagnostic_results: Mapping[str, Sequence[Mapping[str, Any]]],
    baseline_questions: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Reconcile diagnostic control rankings with committed development baselines."""

    baseline_by_id = {
        row["id"]: row
        for row in baseline_questions
        if isinstance(row.get("id"), str)
    }
    if len(baseline_by_id) != len(baseline_questions):
        raise ValueError("Every baseline development row needs a unique id")
    if len(questions) != len(baseline_questions):
        raise ValueError("Diagnostic and baseline development question counts differ")

    answerable_questions = [
        question
        for question in questions
        if question.get("category") in {"direct", "paraphrased"}
    ]
    answerable_by_id = {
        str(question["id"]): question for question in answerable_questions
    }
    answerable_ids: list[str] = []
    for question in answerable_questions:
        question_id = question.get("id")
        if not isinstance(question_id, str) or question_id not in diagnostic_results:
            raise ValueError("Every development question needs diagnostic results")
        if question_id not in baseline_by_id:
            raise ValueError("Every development question needs a baseline row")
        answerable_ids.append(question_id)

    baseline_ranks: list[int | None] = []
    diagnostic_ranks: list[int | None] = []
    differing_ordinals: list[dict[str, int | None]] = []
    identical_rank_count = 0
    for ordinal, question_id in enumerate(answerable_ids, start=1):
        baseline_rank = baseline_by_id[question_id].get("label_rank")
        if baseline_rank is not None and (
            not isinstance(baseline_rank, int)
            or isinstance(baseline_rank, bool)
            or baseline_rank < 1
        ):
            raise ValueError("Baseline label_rank must be null or a positive integer")
        question = answerable_by_id[question_id]
        labels = question.get("relevant", [])
        if not isinstance(labels, list):
            raise ValueError("Development question relevant labels must be a list")
        diagnostic_rank = first_relevant_rank(
            diagnostic_results[question_id][:5],
            labels,
        )
        baseline_ranks.append(baseline_rank)
        diagnostic_ranks.append(diagnostic_rank)
        if baseline_rank == diagnostic_rank:
            identical_rank_count += 1
        else:
            differing_ordinals.append(
                {
                    "ordinal": ordinal,
                    "baseline_rank": baseline_rank,
                    "diagnostic_rank": diagnostic_rank,
                }
            )

    def rank_metrics(ranks: Sequence[int | None]) -> dict[str, int | float]:
        return {
            "hit_at_5_successes": sum(
                rank is not None and rank <= 5 for rank in ranks
            ),
            "mrr": sum(1 / rank if rank is not None else 0.0 for rank in ranks)
            / len(ranks)
            if ranks
            else 0.0,
        }

    unanswerable_questions = [
        question
        for question in questions
        if question.get("category") not in {"direct", "paraphrased"}
    ]
    has_guard_fields = any(
        any(
            key in baseline_by_id[str(question["id"])]
            for key in ("guard", "guard_decision", "is_sufficient")
        )
        for question in unanswerable_questions
    )
    return {
        "questions_compared": len(answerable_ids),
        "identical_rank_count": identical_rank_count,
        "differing_ranks": differing_ordinals,
        "baseline_label_rank_count": sum(
            rank is not None for rank in baseline_ranks
        ),
        "baseline_metrics": rank_metrics(baseline_ranks),
        "diagnostic_metrics": rank_metrics(diagnostic_ranks),
        "unanswerable_guard_comparison": (
            "available in baseline rows"
            if has_guard_fields
            else "not compared; baseline rows expose no evidence-guard decision"
        ),
        "verdict": (
            "all answerable development ranks match"
            if not differing_ordinals
            else "answerable development ranks differ"
        ),
    }
