"""Dependency-injected runner and deterministic report loading for item 34."""

from __future__ import annotations

import hashlib
import json
import subprocess
from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

from evaluation.end_to_end_checks import (
    RecordedRun,
    format_end_to_end_markdown,
    recorded_run_from_dict,
    recorded_run_from_service_result,
    recorded_run_to_dict,
    summarize_end_to_end,
)

Investigate = Callable[..., Awaitable[Mapping[str, Any]]]


def _answerable(question: Mapping[str, Any]) -> bool:
    answerable = question.get("answerable")
    if isinstance(answerable, bool):
        return answerable
    category = question.get("category")
    if isinstance(category, str):
        return not category.startswith("unanswerable")
    raise ValueError("question has no boolean answerable flag or legacy category")


def load_development_questions(
    questions_file: Path,
    repository_id: str,
    *,
    manifest_path: Path,
) -> list[dict[str, Any]]:
    """Load only the selected repository's manifest-assigned development questions."""

    from evaluation.manifest import manifest_root, questions_for_split, sha256_file

    manifest_path = Path(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    repositories = manifest.get("repositories") if isinstance(manifest, Mapping) else None
    if not isinstance(repositories, list):
        raise ValueError("evaluation manifest has no repository list")
    entry = next(
        (
            candidate
            for candidate in repositories
            if isinstance(candidate, Mapping) and candidate.get("id") == repository_id
        ),
        None,
    )
    if not isinstance(entry, dict):
        raise ValueError(f"{repository_id}: repository is not in the evaluation manifest")
    root = manifest_root(manifest_path)
    question_asset = entry.get("questions")
    if not isinstance(question_asset, Mapping) or not isinstance(question_asset.get("path"), str):
        raise ValueError(f"{repository_id}: manifest has no questions asset")
    relative_path = Path(question_asset["path"])
    if relative_path.is_absolute() or ".." in relative_path.parts:
        raise ValueError(f"{repository_id}: unsafe questions asset path")
    expected_file = (root / relative_path).resolve()
    if not expected_file.is_relative_to(root.resolve()):
        raise ValueError(f"{repository_id}: questions asset escapes the manifest root")
    if Path(questions_file).resolve() != expected_file:
        raise ValueError("questions file must match this repository's manifest asset")
    expected_hash = question_asset.get("sha256")
    if not isinstance(expected_hash, str) or sha256_file(expected_file) != expected_hash:
        raise ValueError(f"{repository_id}: questions asset SHA-256 mismatch")
    split_assignments = entry.get("splits")
    development_ids = (
        split_assignments.get("development") if isinstance(split_assignments, Mapping) else None
    )
    if (
        not isinstance(development_ids, list)
        or any(not isinstance(item, str) for item in development_ids)
        or len(development_ids) != len(set(development_ids))
    ):
        raise ValueError(f"{repository_id}: invalid development split assignment")
    data = json.loads(expected_file.read_text(encoding="utf-8"))
    questions = data.get("questions") if isinstance(data, Mapping) else None
    if not isinstance(questions, list) or any(not isinstance(item, dict) for item in questions):
        raise ValueError("questions file must contain an object list under 'questions'")
    selected = questions_for_split(entry, questions, "development")
    if not selected:
        raise ValueError(f"{repository_id}: manifest has no development questions")
    if len(selected) != len(development_ids):
        raise ValueError(f"{repository_id}: a development question is missing from the file")
    for question in selected:
        question_id = question.get("id")
        if not isinstance(question_id, str) or not question_id:
            raise ValueError("development questions require non-empty string IDs")
        _answerable(question)
    return selected


async def run_end_to_end(
    questions: Sequence[Mapping[str, Any]],
    *,
    repository_id: str,
    questions_file: Path,
    repository_code_commit: str,
    model_names: Mapping[str, str],
    generation_parameters: Mapping[str, Any],
    output_path: Path,
    investigate: Investigate,
    limit: int | None = None,
    provider_error_types: tuple[type[Exception], ...] = (TimeoutError,),
) -> dict[str, Any]:
    """Run each selected development question three times and save every run."""

    if limit is not None and limit < 1:
        raise ValueError("limit must be positive")
    if not repository_code_commit:
        raise ValueError("repository_code_commit must not be empty")
    question_rows: list[tuple[str, bool, str]] = []
    seen_ids: set[str] = set()
    for question in questions:
        question_id = question.get("id")
        query = question.get("question")
        if not isinstance(question_id, str) or not question_id:
            raise ValueError("every question requires a non-empty string id")
        if question_id in seen_ids:
            raise ValueError(f"duplicate question id: {question_id}")
        if not isinstance(query, str) or not query.strip():
            raise ValueError(f"{question_id}: question must be non-empty text")
        seen_ids.add(question_id)
        question_rows.append((question_id, _answerable(question), query))

    selected = question_rows if limit is None else question_rows[:limit]
    skipped = [
        {"question_id": question_id, "reason": "omitted by --limit"}
        for question_id, _, _ in question_rows[len(selected) :]
    ]
    all_runs: list[dict[str, Any]] = []
    for question_id, answerable, query in selected:
        for repeat_index in (1, 2, 3):
            try:
                result = await investigate(
                    repository_id,
                    query,
                    persist=True,
                    temperature=0,
                )
            except provider_error_types as exc:
                error_class = getattr(exc, "error_class", type(exc).__name__)
                run = RecordedRun(
                    question_id=question_id,
                    answerable=answerable,
                    outcome="error",
                    citations=(),
                    retrieved_chunk_ids=frozenset(),
                    retrieved_chunk_texts={},
                    repeat_index=repeat_index,
                    error_classes=(str(error_class),),
                )
                raw_result: Mapping[str, Any] = {
                    "outcome": "error",
                    "error_class": str(error_class),
                }
            else:
                if not isinstance(result, Mapping):
                    raise ValueError("investigation service result must be an object")
                run = recorded_run_from_service_result(
                    question_id,
                    answerable,
                    repeat_index,
                    result,
                )
                raw_result = result
            all_runs.append(
                {
                    "record": recorded_run_to_dict(run),
                    "raw_run": dict(raw_result),
                }
            )

    record_set = {
        "metadata": {
            "schema_version": 1,
            "questions_file": str(questions_file),
            "questions_sha256": hashlib.sha256(Path(questions_file).read_bytes()).hexdigest(),
            "repository_id": repository_id,
            "repository_code_commit": repository_code_commit,
            "model_names": dict(sorted(model_names.items())),
            "generation_parameters": dict(sorted(generation_parameters.items())),
            "repeat_count": 3,
            "temperature": 0,
        },
        "runs": all_runs,
        "skipped_questions": skipped,
    }
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(record_set, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return record_set


def _read_record_set(path: Path) -> tuple[list[RecordedRun], list[dict[str, str]]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, Mapping) or not isinstance(data.get("metadata"), Mapping):
        raise ValueError(f"{path}: not an end-to-end run-set record")
    runs = data.get("runs")
    skipped = data.get("skipped_questions")
    if not isinstance(runs, list) or not isinstance(skipped, list):
        raise ValueError(f"{path}: runs and skipped_questions must be lists")
    records: list[RecordedRun] = []
    for item in runs:
        if not isinstance(item, Mapping) or not isinstance(item.get("record"), Mapping):
            raise ValueError(f"{path}: each run must contain a record object")
        records.append(recorded_run_from_dict(item["record"]))
    skipped_rows = [
        {
            "source_file": path.name,
            "question_id": str(item.get("question_id", "")),
            "reason": str(item.get("reason", "")),
        }
        for item in skipped
        if isinstance(item, Mapping)
    ]
    return records, skipped_rows


def report_run_sets(
    records_path: Path,
    *,
    generated_at: str | None = None,
) -> tuple[dict[str, Any], str]:
    """Read one record file or a directory and build reproducible JSON and Markdown."""

    records_path = Path(records_path)
    paths = sorted(records_path.glob("*.json")) if records_path.is_dir() else [records_path]
    if not paths:
        raise ValueError(f"no JSON run-set files found at {records_path}")
    all_records: list[RecordedRun] = []
    skipped: list[dict[str, str]] = []
    for path in paths:
        records, skipped_rows = _read_record_set(path)
        prefix = path.stem if len(paths) > 1 else None
        all_records.extend(
            replace(record, question_id=f"{prefix}:{record.question_id}")
            if prefix is not None
            else record
            for record in records
        )
        skipped.extend(skipped_rows)
    summary = summarize_end_to_end(all_records)
    report_data: dict[str, Any] = {
        "run_set_count": len(paths),
        "source_files": [path.name for path in paths],
        "skipped_question_count": len(skipped),
        "skipped_questions": sorted(
            skipped,
            key=lambda row: (row["source_file"], row["question_id"], row["reason"]),
        ),
        "summary": summary,
    }
    if generated_at is not None:
        report_data["generated_at"] = generated_at
    markdown = format_end_to_end_markdown(
        {
            **summary,
            "skipped_question_count": len(skipped),
            "provider_error_class_counts": summary["check_c"]["provider_error_class_counts"],
        },
        generated_at=generated_at,
        skipped_questions=report_data["skipped_questions"],
    )
    return report_data, markdown


def current_repository_commit(repository_root: Path) -> str:
    """Return the checked-out repository commit for run metadata."""

    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=repository_root,
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()
