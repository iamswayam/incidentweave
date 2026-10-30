from __future__ import annotations

import pytest

from evaluation.test_file_diagnostic import (
    build_repository_diagnostic,
    reconcile_control,
    summarize_fixture_paths,
    summarize_question_results,
)


def test_summarize_fixture_paths_counts_chunks_and_sorts_distinct_paths() -> None:
    chunks = [
        {"file_path": "tests/test_api.py"},
        {"file_path": "tests/test_api.py"},
        {"file_path": "src/latest_report.py"},
        {"file_path": "src/testament/guide.md"},
    ]

    assert summarize_fixture_paths(chunks) == {
        "total_chunks": 4,
        "tagged_chunk_count": 2,
        "tagged_chunk_share": 0.5,
        "tagged_paths": ["tests/test_api.py"],
        "untagged_test_paths": [
            "src/latest_report.py",
            "src/testament/guide.md",
        ],
    }


def test_summarize_fixture_paths_rejects_missing_paths() -> None:
    with pytest.raises(ValueError, match="file_path"):
        summarize_fixture_paths([{"content": "missing path"}])


def test_summarize_question_results_counts_tagged_top_five_and_test_evidence_hits() -> None:
    questions = [
        {
            "id": "dev-a",
            "category": "direct",
            "relevant_spans": [
                {"file_path": "tests/test_api.py", "line_start": 10, "line_end": 12}
            ],
        },
        {
            "id": "dev-b",
            "category": "paraphrased",
            "relevant_spans": [
                {"file_path": "app/service.py", "line_start": 3, "line_end": 5}
            ],
        },
        {
            "id": "dev-c",
            "category": "unanswerable_near",
            "relevant_spans": [],
        },
    ]
    results = {
        "dev-a": [
            {"file_path": "tests/test_api.py", "line_start": 11, "line_end": 15},
            {"file_path": "app/service.py"},
        ],
        "dev-b": [
            {"file_path": "tests/test_api.py"},
            {"file_path": "app/other.py"},
        ],
        "dev-c": [{"file_path": "specs/test_contract.yml"}],
    }

    assert summarize_question_results(questions, results) == {
        "development_question_count": 3,
        "question_top5_test_counts": [1, 1, 1],
        "top5_test_chunk_count": 3,
        "top5_result_count": 5,
        "top5_test_share": 0.6,
        "answerable_test_evidence_question_count": 1,
        "answerable_test_evidence_hit_at_5": 1,
    }


def test_summarize_question_results_requires_every_selected_question() -> None:
    with pytest.raises(ValueError, match="retrieval results"):
        summarize_question_results(
            [{"id": "dev-a", "category": "unanswerable_near"}],
            {},
        )


def test_build_repository_diagnostic_combines_summaries() -> None:
    summary = build_repository_diagnostic(
        [{"file_path": "tests/test_a.py"}, {"file_path": "app/a.py"}],
        [{"id": "dev-a", "category": "unanswerable_near", "relevant_spans": []}],
        {"dev-a": [{"file_path": "tests/test_a.py"}]},
    )

    assert summary["total_chunks"] == 2
    assert summary["tagged_chunk_share"] == 0.5
    assert summary["top5_test_share"] == 1.0


def test_reconcile_control_compares_answerable_ranks_and_aggregates() -> None:
    questions = [
        {
            "id": "dev-a",
            "category": "direct",
            "relevant": [{"file_path": "app/a.py", "substring": "needle"}],
        },
        {
            "id": "dev-b",
            "category": "paraphrased",
            "relevant": [{"file_path": "app/b.py", "substring": "missing"}],
        },
        {"id": "dev-c", "category": "unanswerable_near", "relevant": []},
    ]
    diagnostic_results = {
        "dev-a": [{"file_path": "app/a.py", "content": "found needle"}],
        "dev-b": [{"file_path": "app/b.py", "content": "nothing here"}],
        "dev-c": [{"file_path": "app/c.py", "content": "no evidence"}],
    }
    baseline_questions = [
        {"id": "dev-a", "label_rank": 2},
        {"id": "dev-b", "label_rank": None},
        {"id": "dev-c", "label_rank": None},
    ]

    reconciliation = reconcile_control(
        questions,
        diagnostic_results,
        baseline_questions,
    )

    assert reconciliation == {
        "questions_compared": 2,
        "identical_rank_count": 1,
        "differing_ranks": [
            {"ordinal": 1, "baseline_rank": 2, "diagnostic_rank": 1}
        ],
        "baseline_label_rank_count": 1,
        "baseline_metrics": {"hit_at_5_successes": 1, "mrr": 0.25},
        "diagnostic_metrics": {"hit_at_5_successes": 1, "mrr": 0.5},
        "unanswerable_guard_comparison": (
            "not compared; baseline rows expose no evidence-guard decision"
        ),
        "verdict": "answerable development ranks differ",
    }


def test_reconcile_control_reports_matching_answerable_ranks() -> None:
    questions = [
        {
            "id": "dev-a",
            "category": "direct",
            "relevant": [{"file_path": "app/a.py", "substring": "needle"}],
        }
    ]

    reconciliation = reconcile_control(
        questions,
        {"dev-a": [{"file_path": "app/a.py", "content": "found needle"}]},
        [{"id": "dev-a", "label_rank": 1}],
    )

    assert reconciliation["questions_compared"] == 1
    assert reconciliation["identical_rank_count"] == 1
    assert reconciliation["baseline_label_rank_count"] == 1
    assert reconciliation["differing_ranks"] == []
    assert reconciliation["baseline_metrics"] == {
        "hit_at_5_successes": 1,
        "mrr": 1.0,
    }
    assert reconciliation["diagnostic_metrics"] == {
        "hit_at_5_successes": 1,
        "mrr": 1.0,
    }
    assert reconciliation["verdict"] == "all answerable development ranks match"
