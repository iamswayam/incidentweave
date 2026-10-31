from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.build_fixture import load_fixture, write_fixture
from evaluation.metrics import is_relevant_span, span_hit_at_k, span_mrr
from evaluation.retrieval_eval import compare_reports
from evaluation.span_labels import derive_spans, find_span
from evaluation.stats import exact_sign_test, paired_comparison, wilson_interval


def test_exact_sign_test_and_paired_comparison() -> None:
    assert exact_sign_test(4, 0) == 0.125
    assert paired_comparison([True, False, True], [False, True, True]) == {
        "wins": 1,
        "losses": 1,
        "ties": 1,
        "p_value": 1.0,
    }


def test_wilson_intervals_match_known_values_and_empty_input() -> None:
    low, high = wilson_interval(11, 16)
    assert low == pytest.approx(0.44, abs=0.01)
    assert high == pytest.approx(0.86, abs=0.01)
    low, high = wilson_interval(15, 16)
    assert low == pytest.approx(0.72, abs=0.01)
    assert high == pytest.approx(0.99, abs=0.01)
    assert wilson_interval(0, 0) == (0.0, 1.0)


def test_find_span_single_line_case_insensitive_and_first_occurrence() -> None:
    assert find_span("Alpha\nalpha", "ALPHA") == (1, 1)


def test_find_span_multiline() -> None:
    assert find_span("before\nStart Here\nThen finish\nafter", "start here\nthen finish") == (
        2,
        3,
    )


def test_find_span_returns_none_when_missing() -> None:
    assert find_span("some source", "not present") is None


def test_derive_spans_reads_pinned_paths_and_keeps_empty_questions() -> None:
    golden = {
        "pinned_sha": "abc123",
        "questions": [
            {
                "id": "answerable",
                "relevant": [{"file_path": "a.py", "substring": "needle"}],
            },
            {"id": "unanswerable", "relevant": []},
        ],
    }
    calls: list[tuple[str, str]] = []

    def read_file(sha: str, path: str) -> str:
        calls.append((sha, path))
        return "needle"

    assert derive_spans(golden, read_file) == {
        "answerable": [
            {"file_path": "a.py", "line_start": 1, "line_end": 1}
        ],
        "unanswerable": [],
    }
    assert calls == [("abc123", "a.py")]


def test_span_relevance_requires_overlap_same_file_and_not_adjacency() -> None:
    spans = [{"file_path": "a.py", "line_start": 3, "line_end": 5}]
    assert is_relevant_span(
        {"file_path": "a.py", "line_start": 5, "line_end": 8}, spans
    )
    assert not is_relevant_span(
        {"file_path": "a.py", "line_start": 6, "line_end": 8}, spans
    )
    assert not is_relevant_span(
        {"file_path": "b.py", "line_start": 3, "line_end": 5}, spans
    )


def test_span_hit_at_k_and_mrr() -> None:
    results = [
        [
            {"file_path": "a.py", "line_start": 10, "line_end": 12},
            {"file_path": "a.py", "line_start": 2, "line_end": 4},
        ],
        [{"file_path": "b.py", "line_start": 1, "line_end": 1}],
    ]
    spans = [
        [{"file_path": "a.py", "line_start": 3, "line_end": 3}],
        [{"file_path": "b.py", "line_start": 7, "line_end": 8}],
    ]

    assert span_hit_at_k(results, spans, 1) == 0
    assert span_hit_at_k(results, spans, 3) == 1
    assert span_mrr(results, spans) == pytest.approx(0.25)


def test_fixture_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "fixture.json.gz"
    fixture = {
        "meta": {"pinned_sha": "sha", "chunk_count": 1},
        "chunks": [{"file_path": "a.py", "embedding": [0.1]}],
        "queries": {"q1": [0.2]},
    }

    size = write_fixture(fixture, path)

    assert size == path.stat().st_size
    assert load_fixture(path) == fixture


def test_compare_reports_runs_paired_exact_test() -> None:
    report_a = {
        "questions": [
            {"id": "q1", "category": "direct", "label_hits": {"5": True}},
            {"id": "q2", "category": "paraphrased", "label_hits": {"5": False}},
            {"id": "q3", "category": "direct", "label_hits": {"5": False}},
            {"id": "q4", "category": "unanswerable_far", "label_hits": {"5": False}},
        ]
    }
    report_b = {
        "questions": [
            {"id": "q1", "category": "direct", "label_hits": {"5": True}},
            {"id": "q2", "category": "paraphrased", "label_hits": {"5": True}},
            {"id": "q3", "category": "direct", "label_hits": {"5": False}},
            {"id": "q4", "category": "unanswerable_far", "label_hits": {"5": True}},
        ]
    }

    assert compare_reports(report_a, report_b, k=5) == {
        "wins": 1,
        "losses": 0,
        "ties": 2,
        "p_value": 1.0,
    }
