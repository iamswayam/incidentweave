"""Adapt saved development run records to framework-neutral RAG evaluation samples."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any


def load_offline_eval_data(
    run_files: Sequence[str | Path],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Load successful answer records and summarize the supplied development run files."""

    if not run_files:
        raise ValueError("at least one development run file is required")

    samples: list[dict[str, Any]] = []
    repos_covered: set[str] = set()
    skipped_by_reason = {"non_success_outcome": 0, "missing_answer": 0}
    total_records = 0

    for run_file in run_files:
        path = Path(run_file)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"{path}: cannot load development run records: {exc}") from exc
        if not isinstance(data, Mapping):
            raise ValueError(f"{path}: run file must contain an object")

        metadata = data.get("metadata")
        if not isinstance(metadata, Mapping):
            raise ValueError(f"{path}: run file metadata must be an object")
        repository_id = metadata.get("repository_id")
        if not isinstance(repository_id, str) or not repository_id:
            raise ValueError(f"{path}: metadata must contain a repository_id")
        repos_covered.add(repository_id)

        runs = data.get("runs")
        if not isinstance(runs, list):
            raise ValueError(f"{path}: runs must be a list")
        for index, run in enumerate(runs):
            if not isinstance(run, Mapping) or not isinstance(run.get("record"), Mapping):
                raise ValueError(f"{path}: runs[{index}] must contain a record object")
            record = run["record"]
            total_records += 1
            raw_run = run.get("raw_run")
            raw_run = raw_run if isinstance(raw_run, Mapping) else {}
            outcome = record.get("outcome")
            if outcome not in {"success", "answered"}:
                skipped_by_reason["non_success_outcome"] += 1
                continue

            answer = record.get("answer")
            if answer is None and outcome == "answered":
                answer = raw_run.get("diagnosis")
            if not isinstance(answer, str) or not answer.strip():
                skipped_by_reason["missing_answer"] += 1
                continue

            question = record.get("query")
            if question is None:
                question = raw_run.get("query")
            if not isinstance(question, str) or not question.strip():
                raise ValueError(f"{path}: runs[{index}] answered record has no query")
            evidence = record.get("evidence", [])
            if "evidence" not in record and outcome == "answered":
                evidence = raw_run.get("retrieval_results", [])
            if not isinstance(evidence, list):
                raise ValueError(f"{path}: runs[{index}] evidence must be a list")
            contexts = []
            for evidence_index, item in enumerate(evidence):
                if isinstance(item, Mapping) and isinstance(item.get("content"), str):
                    contexts.append(item["content"])
                elif isinstance(item, Mapping) and isinstance(item.get("text"), str):
                    contexts.append(item["text"])
                else:
                    raise ValueError(
                        f"{path}: runs[{index}] evidence[{evidence_index}] "
                        "must contain string content"
                    )

            samples.append(
                {
                    "question": question,
                    "answer": answer,
                    "contexts": contexts,
                    "ground_truth": None,
                }
            )

    summary = {
        "total_records": total_records,
        "success_count": len(samples),
        "skipped_count": total_records - len(samples),
        "repos_covered": sorted(repos_covered),
        "skipped_by_reason": skipped_by_reason,
    }
    return samples, summary
