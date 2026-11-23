from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.offline_eval_adapter import load_offline_eval_data


def _write_run_file(
    path: Path,
    repository_id: str,
    records: list[dict[str, Any]],
) -> Path:
    path.write_text(
        json.dumps(
            {
                "metadata": {"repository_id": repository_id},
                "runs": [{"record": record} for record in records],
            }
        ),
        encoding="utf-8",
    )
    return path


def test_adapter_keeps_only_success_records_and_builds_contexts(tmp_path: Path) -> None:
    path = _write_run_file(
        tmp_path / "development.json",
        "rq",
        [
            {
                "outcome": "success",
                "query": "Where is the handler defined?",
                "answer": "It is in src/handler.py.",
                "evidence": [{"content": "def handle_request():"}],
            },
            {"outcome": "generation_unavailable"},
            {"outcome": "guard_refused"},
            {"outcome": "error"},
        ],
    )

    samples, summary = load_offline_eval_data([path])

    assert samples == [
        {
            "question": "Where is the handler defined?",
            "answer": "It is in src/handler.py.",
            "contexts": ["def handle_request():"],
            "ground_truth": None,
        }
    ]
    assert summary == {
        "total_records": 4,
        "success_count": 1,
        "skipped_count": 3,
        "repos_covered": ["rq"],
        "skipped_by_reason": {"non_success_outcome": 3, "missing_answer": 0},
    }


def test_adapter_skips_success_records_with_missing_or_null_answers(tmp_path: Path) -> None:
    path = _write_run_file(
        tmp_path / "development.json",
        "client_python",
        [
            {"outcome": "success", "query": "Missing answer"},
            {"outcome": "success", "query": "Null answer", "answer": None},
        ],
    )

    samples, summary = load_offline_eval_data([path])

    assert samples == []
    assert summary["total_records"] == 2
    assert summary["success_count"] == 0
    assert summary["skipped_count"] == 2
    assert summary["repos_covered"] == ["client_python"]
    assert summary["skipped_by_reason"]["missing_answer"] == 2


def test_adapter_handles_current_end_to_end_runner_records(tmp_path: Path) -> None:
    path = tmp_path / "development.json"
    path.write_text(
        json.dumps(
            {
                "metadata": {"repository_id": "kopf"},
                "runs": [
                    {
                        "record": {"outcome": "answered"},
                        "raw_run": {
                            "query": "What triggers this retry?",
                            "diagnosis": "The retry is triggered after a timeout.",
                            "retrieval_results": [{"content": "if timed_out: retry()"}],
                        },
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    samples, summary = load_offline_eval_data([path])

    assert samples == [
        {
            "question": "What triggers this retry?",
            "answer": "The retry is triggered after a timeout.",
            "contexts": ["if timed_out: retry()"],
            "ground_truth": None,
        }
    ]
    assert summary["total_records"] == 1
    assert summary["success_count"] == 1
    assert summary["skipped_count"] == 0
    assert summary["repos_covered"] == ["kopf"]
