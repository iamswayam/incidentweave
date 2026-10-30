"""Pure helpers for the test-file retrieval diagnostic."""

from __future__ import annotations

import math
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


def _result_identity(result: Mapping[str, Any]) -> tuple[str, int, int]:
    path = result.get("file_path")
    line_start = result.get("line_start")
    line_end = result.get("line_end")
    if (
        not isinstance(path, str)
        or not isinstance(line_start, int)
        or isinstance(line_start, bool)
        or not isinstance(line_end, int)
        or isinstance(line_end, bool)
    ):
        raise ValueError("Retrieved results need file_path and integer line bounds")
    return path, line_start, line_end


def reconcile_control(
    questions: Sequence[Mapping[str, Any]],
    diagnostic_results: Mapping[str, Sequence[Mapping[str, Any]]],
    baseline_questions: Sequence[Mapping[str, Any]],
    baseline_aggregates: Mapping[str, Any],
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

    question_ids: list[str] = []
    for question in questions:
        question_id = question.get("id")
        if not isinstance(question_id, str) or question_id not in diagnostic_results:
            raise ValueError("Every development question needs diagnostic results")
        if question_id not in baseline_by_id:
            raise ValueError("Every development question needs a baseline row")
        question_ids.append(question_id)

    baseline_has_results = all(
        isinstance(baseline_by_id[question_id].get("retrieved"), list)
        for question_id in question_ids
    )
    if baseline_has_results:
        differing_ordinals: list[int] = []
        identical_count = 0
        for ordinal, question_id in enumerate(question_ids, start=1):
            diagnostic = diagnostic_results[question_id][:5]
            baseline = baseline_by_id[question_id]["retrieved"][:5]
            if [_result_identity(row) for row in diagnostic] == [
                _result_identity(row) for row in baseline
            ]:
                identical_count += 1
            else:
                differing_ordinals.append(ordinal)
        return {
            "mode": "top_five",
            "questions_compared": len(question_ids),
            "identical_count": identical_count,
            "differing_ordinals": differing_ordinals,
            "verdict": (
                "all development top-five lists match"
                if not differing_ordinals
                else "development top-five lists differ"
            ),
        }

    substring_aggregates = baseline_aggregates.get("substring_labels")
    baseline_hit_at_5 = (
        substring_aggregates.get("hit_at_5")
        if isinstance(substring_aggregates, Mapping)
        else None
    )
    expected_count = (
        substring_aggregates.get("count")
        if isinstance(substring_aggregates, Mapping)
        else None
    )
    expected_successes = (
        baseline_hit_at_5.get("successes")
        if isinstance(baseline_hit_at_5, Mapping)
        else None
    )
    expected_mrr = (
        substring_aggregates.get("mrr")
        if isinstance(substring_aggregates, Mapping)
        else None
    )
    if (
        expected_count != len(questions)
        or not isinstance(expected_successes, int)
        or isinstance(expected_successes, bool)
        or not isinstance(expected_mrr, (int, float))
        or isinstance(expected_mrr, bool)
    ):
        raise ValueError("Baseline development substring-label aggregates are invalid")

    reciprocal_ranks: list[float] = []
    hit_at_5_successes = 0
    for question, question_id in zip(questions, question_ids):
        labels = question.get("relevant", [])
        if not isinstance(labels, list):
            raise ValueError("Development question relevant labels must be a list")
        rank = first_relevant_rank(diagnostic_results[question_id][:5], labels)
        if rank is not None:
            hit_at_5_successes += 1
            reciprocal_ranks.append(1 / rank)
        else:
            reciprocal_ranks.append(0.0)
    observed_mrr = sum(reciprocal_ranks) / len(reciprocal_ranks)
    observed_matches = hit_at_5_successes == expected_successes and math.isclose(
        observed_mrr,
        float(expected_mrr),
        rel_tol=0.0,
        abs_tol=1e-12,
    )
    return {
        "mode": "aggregate_metrics",
        "questions_compared": len(questions),
        "identical_count": None,
        "differing_ordinals": [],
        "baseline_hit_at_5_successes": expected_successes,
        "diagnostic_hit_at_5_successes": hit_at_5_successes,
        "baseline_mrr": float(expected_mrr),
        "diagnostic_mrr": observed_mrr,
        "verdict": (
            "development hit@5 and MRR aggregates match"
            if observed_matches
            else "development hit@5 and/or MRR aggregates differ"
        ),
    }
