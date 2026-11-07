from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evaluation.end_to_end_runner import run_end_to_end
from scripts.run_end_to_end import main


@pytest.mark.anyio
async def test_report_subcommand_writes_markdown_and_json_from_fake_run(tmp_path: Path) -> None:
    async def fake_investigate(
        repository: str,
        query: str,
        **kwargs: Any,
    ) -> dict[str, Any]:
        return {
            "outcome": "refused_guard",
            "retrieval_results": [],
            "generation_trace": None,
            "retry_used": False,
        }

    questions_file = tmp_path / "questions.json"
    questions_file.write_text("synthetic", encoding="utf-8")
    record_path = tmp_path / "records.json"
    await run_end_to_end(
        [{"id": "q1", "question": "synthetic unanswerable question", "answerable": False}],
        repository_id="sample",
        questions_file=questions_file,
        repository_code_commit="abc123",
        model_names={"generation": "fake"},
        generation_parameters={"temperature": 0},
        output_path=record_path,
        investigate=fake_investigate,
    )
    markdown_path = tmp_path / "report.md"
    json_path = tmp_path / "summary.json"

    assert (
        main(
            [
                "report",
                str(record_path),
                "--out-md",
                str(markdown_path),
                "--out-json",
                str(json_path),
            ]
        )
        == 0
    )

    markdown = markdown_path.read_text(encoding="utf-8")
    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert "refusal correctness" in markdown
    assert "False-answer rate: 0.000 (0/3)" in markdown
    assert "record_count" in summary["summary"]
