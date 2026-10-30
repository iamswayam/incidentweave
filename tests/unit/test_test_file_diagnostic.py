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


def test_reconcile_control_compares_top_five_identities_and_reports_ordinals() -> None:
    questions = [
        {"id": "dev-a"},
        {"id": "dev-b"},
    ]
    first = {"file_path": "app/a.py", "line_start": 1, "line_end": 5}
    second = {"file_path": "app/b.py", "line_start": 6, "line_end": 10}
    diagnostic_results = {"dev-a": [first], "dev-b": [second]}
    baseline_questions = [
        {"id": "dev-a", "retrieved": [dict(first)]},
        {"id": "dev-b", "retrieved": [dict(first)]},
    ]

    reconciliation = reconcile_control(
        questions,
        diagnostic_results,
        baseline_questions,
        {},
    )

    assert reconciliation == {
        "mode": "top_five",
        "questions_compared": 2,
        "identical_count": 1,
        "differing_ordinals": [2],
        "verdict": "development top-five lists differ",
    }


def test_reconcile_control_falls_back_to_development_aggregates() -> None:
    questions = [
        {
            "id": "dev-a",
            "relevant": [{"file_path": "app/a.py", "substring": "needle"}],
        },
        {"id": "dev-b", "relevant": []},
    ]
    diagnostic_results = {
        "dev-a": [{"file_path": "app/a.py", "content": "found needle"}],
        "dev-b": [{"file_path": "app/b.py", "content": "nothing"}],
    }
    baseline_questions = [{"id": "dev-a"}, {"id": "dev-b"}]
    aggregates = {
        "substring_labels": {
            "count": 2,
            "hit_at_5": {"successes": 1},
            "mrr": 0.5,
        }
    }

    reconciliation = reconcile_control(
        questions,
        diagnostic_results,
        baseline_questions,
        aggregates,
    )

    assert reconciliation == {
        "mode": "aggregate_metrics",
        "questions_compared": 2,
        "identical_count": None,
        "differing_ordinals": [],
        "baseline_hit_at_5_successes": 1,
        "diagnostic_hit_at_5_successes": 1,
        "baseline_mrr": 0.5,
        "diagnostic_mrr": 0.5,
        "verdict": "development hit@5 and MRR aggregates match",
    }
