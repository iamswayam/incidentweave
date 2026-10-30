"""Pure helpers for the test-file retrieval diagnostic."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from evaluation.metrics import first_relevant_span_rank
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
