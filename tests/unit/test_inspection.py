from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pytest

from evaluation import retrieval_eval
from evaluation.inspection import (
    render_repository_summary,
    render_strategy_report,
)
from scripts import inspect_retrieval


def _retrieved(
    rank: int,
    *,
    line_start: int,
    line_end: int,
    content: str,
    vector_score: float | None,
    fts_score: float | None,
    rrf_score: float,
) -> dict[str, Any]:
    return {
        "rank": rank,
        "file_path": "src/example.py",
        "line_start": line_start,
        "line_end": line_end,
        "content": content,
        "vector_score": vector_score,
        "fts_score": fts_score,
        "rrf_score": rrf_score,
    }


@pytest.fixture
def inspection_data() -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    questions = [
        {
            "id": "hit-01",
            "category": "direct",
            "question": "Where is the useful code?",
            "relevant_spans": [
                {
                    "file_path": "src/example.py",
                    "line_start": 2,
                    "line_end": 4,
                }
            ],
        },
        {
            "id": "miss-01",
            "category": "paraphrased",
            "question": "Explain the missing behavior.",
            "relevant_spans": [
                {
                    "file_path": "src/example.py",
                    "line_start": 8,
                    "line_end": 8,
                }
            ],
        },
        {
            "id": "unknown-01",
            "category": "unanswerable_far",
            "question": "What is not in this repository?",
            "relevant_spans": [],
        },
    ]
    report = {
        "metadata": {
            "repo_id": "synthetic-repo",
            "split": "development",
            "previously_exposed": False,
        },
        "questions": [
            {
                "id": "hit-01",
                "category": "direct",
                "span_rank": 2,
                "retrieved": [
                    _retrieved(
                        1,
                        line_start=1,
                        line_end=1,
                        content="unrelated = True",
                        vector_score=0.7,
                        fts_score=None,
                        rrf_score=0.016,
                    ),
                    _retrieved(
                        2,
                        line_start=2,
                        line_end=4,
                        content="x" * 20 + " | " + "y" * 70,
                        vector_score=0.4,
                        fts_score=0.25,
                        rrf_score=0.032,
                    ),
                ],
            },
            {
                "id": "miss-01",
                "category": "paraphrased",
                "span_rank": None,
                "retrieved": [
                    _retrieved(
                        rank,
                        line_start=10 + rank,
                        line_end=10 + rank,
                        content=f"distractor_{rank} = True",
                        vector_score=0.8 + rank / 100,
                        fts_score=0.1,
                        rrf_score=0.02,
                    )
                    for rank in range(1, 6)
                ],
            },
            {
                "id": "unknown-01",
                "category": "unanswerable_far",
                "span_rank": None,
                "retrieved": [
                    _retrieved(
                        1,
                        line_start=1,
                        line_end=1,
                        content="unrelated = True",
                        vector_score=0.8,
                        fts_score=None,
                        rrf_score=0.016,
                    )
                ],
            },
        ],
    }
    fixture = {
        "meta": {"chunk_count": 2},
        "chunks": [
            {
                "file_path": "src/example.py",
                "line_start": 1,
                "line_end": 2,
                "content": "first line\nline | two",
                "embedding": [0.1],
            },
            {
                "file_path": "src/example.py",
                "line_start": 2,
                "line_end": 2,
                "content": "line | two",
                "embedding": [0.2],
            },
        ],
        "queries": {},
    }
    return report, questions, fixture


def _render(
    data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> str:
    report, questions, fixture = data
    return render_strategy_report(
        report,
        questions,
        fixture,
        fixture,
        strategy="s0_lines_60_10",
        split="development",
        fixture_sha256="0123456789abcdef",
    )


def test_render_strategy_report_includes_hit_miss_and_unanswerable_cards(
    inspection_data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> None:
    rendered = _render(inspection_data)

    assert "### hit-01 | direct | HIT at rank 2" in rendered
    assert "### miss-01 | paraphrased | MISS" in rendered
    assert "### unknown-01 | unanswerable_far | no answer expected" in rendered
    assert "**Why it missed (fill in by hand):** ______" in rendered
    assert (
        "Expected: refuse. If the guard would answer here, this is a false-answer risk."
        in rendered
    )
    assert "Missed questions: miss-01" in rendered
    assert (
        "**Guard (provisional threshold 0.5):** would answer; "
        "best vector distance: 0.400."
    ) in rendered


def test_render_reconstructs_evidence_and_handles_missing_lines(
    inspection_data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> None:
    rendered = _render(inspection_data)

    assert "`src/example.py:2-4` (3 lines)" in rendered
    assert "2 | line | two" in rendered
    assert "3 | (line not available)" in rendered
    assert "4 | (line not available)" in rendered


def test_render_escapes_pipe_and_truncates_starts_with(
    inspection_data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> None:
    rendered = _render(inspection_data)

    assert ("x" * 20) + " \\| " + ("y" * 37) + "..." in rendered


def test_render_is_deterministic_and_has_exposure_and_heldout_banners(
    inspection_data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> None:
    report, questions, fixture = inspection_data
    report["metadata"]["previously_exposed"] = True
    report["metadata"]["split"] = "held_out"

    first = render_strategy_report(
        report,
        questions,
        fixture,
        fixture,
        strategy="s0_lines_60_10",
        split="held_out",
        fixture_sha256="0123456789abcdef",
    )
    second = render_strategy_report(
        report,
        questions,
        fixture,
        fixture,
        strategy="s0_lines_60_10",
        split="held_out",
        fixture_sha256="0123456789abcdef",
    )

    assert first == second
    assert "**IncidentWeave held-out was previously exposed**" in first
    assert "**HELD-OUT: do not use for design decisions**" in first
    assert "Fixture SHA-256: `0123456789ab`" in first


def test_render_summary_contains_strategy_ranks_totals_and_common_misses(
    inspection_data: tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]],
) -> None:
    report, questions, _fixture = inspection_data
    ast_report = {
        **report,
        "questions": [
            {**record, "span_rank": None}
            if record["id"] == "miss-01"
            else record
            for record in report["questions"]
        ],
    }
    summary = render_repository_summary(
        questions,
        {
            "s0_lines_60_10": report,
            "s2_ast_v1": ast_report,
        },
        repo_id="synthetic-repo",
        split="development",
    )

    assert "| Question | Category | s0_lines_60_10 | s2_ast_v1 |" in summary
    assert "| hit-01 | direct | 2 | 2 |" in summary
    assert "| miss-01 | paraphrased | - | - |" in summary
    assert "| unknown-01 | unanswerable_far | n/a | n/a |" in summary
    assert "Hit@5 1; MRR 0.250" in summary
    assert "Missed under every strategy: miss-01" in summary


def test_cli_refuses_frozen_splits_without_confirmation(
    capsys: pytest.CaptureFixture[str],
) -> None:
    for split in ("held_out", "all"):
        assert inspect_retrieval.main(["--repo", "lifeos", "--split", split]) == 2
        assert "confirm-frozen-heldout" in capsys.readouterr().err


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (["--repo", "not-a-repository"], "not in the evaluation manifest"),
        (["--strategy", "not-a-strategy"], "Unknown strategy"),
    ],
)
def test_cli_rejects_unknown_repository_or_strategy(
    capsys: pytest.CaptureFixture[str],
    arguments: list[str],
    message: str,
) -> None:
    assert inspect_retrieval.main(arguments) == 2
    assert message in capsys.readouterr().err


def test_record_details_adds_full_results_and_defaults_remain_unchanged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fixture = {
        "meta": {"chunk_count": 1, "question_count": 1},
        "chunks": [],
        "queries": {"q1": [0.1]},
    }
    question = {
        "id": "q1",
        "category": "direct",
        "question": "find the function",
        "relevant": [{"file_path": "src/a.py", "substring": "value"}],
        "relevant_spans": [
            {"file_path": "src/a.py", "line_start": 1, "line_end": 1}
        ],
    }

    class FakeSession:
        def __init__(self) -> None:
            self.added: list[Any] = []

        async def __aenter__(self) -> FakeSession:
            return self

        async def __aexit__(self, *_args: object) -> None:
            return None

        def add(self, value: Any) -> None:
            self.added.append(value)

        def add_all(self, _values: list[Any]) -> None:
            return None

        async def flush(self) -> None:
            for value in self.added:
                if isinstance(value, retrieval_eval.Repository):
                    value.id = 1

        async def commit(self) -> None:
            return None

    async def fake_delete(_name: str) -> None:
        return None

    async def fake_search(*_args: Any, **_kwargs: Any) -> list[dict[str, Any]]:
        return [
            {
                "file_path": "src/a.py",
                "line_start": 1,
                "line_end": 1,
                "content": "value = 1",
                "vector_score": 0.25,
                "fts_score": 0.125,
                "rrf_score": 0.032,
            }
        ]

    monkeypatch.setattr(retrieval_eval, "_delete_fixture_repository", fake_delete)
    monkeypatch.setattr(retrieval_eval, "load_fixture", lambda _path: fixture)
    monkeypatch.setattr(
        retrieval_eval,
        "load_golden_set",
        lambda _path: {"pinned_sha": "abc", "questions": [question]},
    )
    monkeypatch.setattr(
        retrieval_eval,
        "questions_for_split",
        lambda *_args, **_kwargs: [question],
    )
    monkeypatch.setattr(retrieval_eval, "AsyncSessionLocal", FakeSession)
    monkeypatch.setattr(retrieval_eval, "hybrid_search", fake_search)
    entry = {
        "id": "repo",
        "fixture": {"path": "fixture.json.gz"},
        "questions": {"path": "questions.json"},
        "splits": {"development": ["q1"]},
    }

    def run(**options: Any) -> dict[str, Any]:
        return asyncio.run(
            retrieval_eval.run_offline_retrieval(
                fixture_path=Path("fixture.json.gz"),
                golden_path=Path("questions.json"),
                repo_id="repo",
                split="development",
                entry=entry,
                **options,
            )
        )

    default_report = run()
    compact_report = run(record_retrieved=True)
    detailed_report = run(record_details=True)

    assert "retrieved" not in default_report["questions"][0]
    assert compact_report["questions"][0]["retrieved"] == [
        {
            "file_path": "src/a.py",
            "line_start": 1,
            "line_end": 1,
        }
    ]
    assert detailed_report["questions"][0]["retrieved"] == [
        {
            "rank": 1,
            "file_path": "src/a.py",
            "line_start": 1,
            "line_end": 1,
            "content": "value = 1",
            "vector_score": 0.25,
            "fts_score": 0.125,
            "rrf_score": 0.032,
        }
    ]
