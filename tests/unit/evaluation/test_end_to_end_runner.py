from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evaluation.end_to_end_runner import (
    load_development_questions,
    report_run_sets,
    run_end_to_end,
)
from evaluation.manifest import sha256_file


class FakeProviderError(RuntimeError):
    error_class = "rate_limited"


def test_question_loader_selects_only_manifest_development_ids(tmp_path: Path) -> None:
    evaluation_dir = tmp_path / "evaluation"
    questions_path = evaluation_dir / "repos" / "sample" / "questions.json"
    questions_path.parent.mkdir(parents=True)
    questions_path.write_text(
        json.dumps(
            {
                "questions": [
                    {"id": "dev-q", "question": "development question", "answerable": True},
                    {"id": "held-q", "question": "held out text", "answerable": False},
                ]
            }
        ),
        encoding="utf-8",
    )
    manifest_path = evaluation_dir / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "repositories": [
                    {
                        "id": "sample",
                        "questions": {
                            "path": "evaluation/repos/sample/questions.json",
                            "sha256": sha256_file(questions_path),
                        },
                        "splits": {
                            "development": ["dev-q"],
                            "held_out": ["held-q"],
                        },
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    questions = load_development_questions(
        questions_path,
        "sample",
        manifest_path=manifest_path,
    )

    assert [question["id"] for question in questions] == ["dev-q"]


def _result(outcome: str = "answered") -> dict[str, Any]:
    raw_text = json.dumps(
        {
            "claims": [
                {
                    "text": "A verified claim.",
                    "evidence": [{"chunk_id": "chunk-1", "quote": "the required quote is long"}],
                }
            ]
        }
    )
    return {
        "outcome": outcome,
        "retrieval_results": [
            {"id": "chunk-1", "content": "the required quote is long in this chunk"}
        ],
        "generation_trace": {"raw_text": raw_text, "error_classes": []},
        "retry_used": False,
    }


@pytest.mark.anyio
async def test_run_writes_three_temperature_zero_records_and_marks_limit_skips(
    tmp_path: Path,
) -> None:
    calls: list[tuple[str, str, dict[str, Any]]] = []

    async def fake_investigate(
        repository: str,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        calls.append((repository, query, kwargs))
        return _result()

    questions_file = tmp_path / "questions.json"
    questions_file.write_text('{"questions":[]}\n', encoding="utf-8")
    output = tmp_path / "records.json"
    record_set = await run_end_to_end(
        [
            {"id": "q1", "question": "first synthetic question", "answerable": True},
            {"id": "q2", "question": "second synthetic question", "answerable": False},
        ],
        repository_id="sample-repository",
        questions_file=questions_file,
        repository_code_commit="abc123",
        model_names={"generation": "fake-model"},
        generation_parameters={"temperature": 0, "persist": True},
        output_path=output,
        investigate=fake_investigate,
        limit=1,
    )

    assert len(record_set["runs"]) == 3
    assert [row["record"]["repeat_index"] for row in record_set["runs"]] == [1, 2, 3]
    assert all(row["record"]["question_id"] == "q1" for row in record_set["runs"])
    assert [call[2] for call in calls] == [
        {"persist": True, "temperature": 0},
        {"persist": True, "temperature": 0},
        {"persist": True, "temperature": 0},
    ]
    assert record_set["metadata"]["questions_sha256"]
    assert record_set["metadata"]["temperature"] == 0
    assert record_set["skipped_questions"] == [
        {"question_id": "q2", "reason": "omitted by --limit"}
    ]
    assert json.loads(output.read_text(encoding="utf-8")) == json.loads(json.dumps(record_set))


@pytest.mark.anyio
async def test_provider_error_is_saved_as_an_error_outcome(tmp_path: Path) -> None:
    async def fake_investigate(
        repository: str,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        raise FakeProviderError("synthetic provider failure")

    questions_file = tmp_path / "questions.json"
    questions_file.write_text("synthetic", encoding="utf-8")
    record_set = await run_end_to_end(
        [{"id": "q1", "question": "synthetic question", "answerable": False}],
        repository_id="sample-repository",
        questions_file=questions_file,
        repository_code_commit="abc123",
        model_names={"generation": "fake-model"},
        generation_parameters={"temperature": 0},
        output_path=tmp_path / "error.json",
        investigate=fake_investigate,
        provider_error_types=(FakeProviderError,),
    )

    assert [row["record"]["outcome"] for row in record_set["runs"]] == ["error"] * 3
    assert [row["record"]["error_classes"] for row in record_set["runs"]] == [["rate_limited"]] * 3


@pytest.mark.anyio
async def test_report_outputs_are_deterministic_and_include_registered_denominators(
    tmp_path: Path,
) -> None:
    async def fake_investigate(
        repository: str,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return _result()

    questions_file = tmp_path / "questions.json"
    questions_file.write_text("synthetic", encoding="utf-8")
    record_path = tmp_path / "run-set.json"
    await run_end_to_end(
        [{"id": "q1", "question": "synthetic question", "answerable": True}],
        repository_id="sample-repository",
        questions_file=questions_file,
        repository_code_commit="abc123",
        model_names={"generation": "fake-model"},
        generation_parameters={"temperature": 0},
        output_path=record_path,
        investigate=fake_investigate,
    )

    first_data, first_markdown = report_run_sets(record_path)
    second_data, second_markdown = report_run_sets(record_path)

    assert json.dumps(first_data, sort_keys=True) == json.dumps(second_data, sort_keys=True)
    assert first_markdown.encode("utf-8") == second_markdown.encode("utf-8")
    assert "Citation quote validity: 1.000 (3/3)" in first_markdown
    assert "Retrieval-grounded citation rate: 1.000 (3/3)" in first_markdown
    assert "False-answer rate:" in first_markdown
    assert "False-refusal rate:" in first_markdown
    assert "Overall correctness:" in first_markdown
    assert "Stable outcomes: 1.000 (1/1)" in first_markdown
    assert "Mean cited-chunk-set pairwise Jaccard: 1.000 (questions=1)" in first_markdown
    assert "Answered/refused flips: 0/1" in first_markdown
    assert "Skipped questions: 0" in first_markdown
