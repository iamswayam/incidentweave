"""V2 evaluation question schema, compatibility conversion, and validation."""

from __future__ import annotations

import re
from collections import Counter
from datetime import date
from pathlib import Path, PurePosixPath
from typing import Any

from app.secret_scan import find_secret
from evaluation.source_paths import is_source_python_path

ANSWERABLE_TYPES = {
    "direct",
    "paraphrase",
    "multi-file",
    "config-env",
    "error-message",
    "how-it-works",
}
UNANSWERABLE_KINDS = {"far", "near-miss", "false-premise"}
SOURCES = {"mined", "drafted", "human"}
LLM_ONLY_REVIEW_STATUS = "llm_only_no_human_review"
TARGETS = {
    "full": {
        "answerable": 30,
        "unanswerable": 10,
        "unanswerable_kinds": {"far": 4, "near-miss": 3, "false-premise": 3},
        "minimum_source": 8,
    },
    "reduced": {
        "answerable": 20,
        "unanswerable": 8,
        "unanswerable_kinds": {"far": 3, "near-miss": 3, "false-premise": 2},
        "minimum_source": 6,
    },
}


def legacy_category(question: dict[str, Any]) -> str:
    """Map v2 labels to the v1 evaluator's answerability categories."""

    if question["answerable"]:
        return "direct" if question["type"] == "direct" else "paraphrased"
    return "unanswerable_far" if question["kind"] == "far" else "unanswerable_near"


def derive_relevant_labels(
    spans: list[dict[str, Any]],
    snapshot_root: Path,
) -> list[dict[str, str]]:
    """Derive content labels from each reviewed span's first nonblank source line."""

    labels: list[dict[str, str]] = []
    root = snapshot_root.resolve()
    for span in spans:
        relative = PurePosixPath(span["file_path"])
        source = (root / Path(*relative.parts)).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(
                f"cannot derive label from missing or unsafe file {span['file_path']!r}"
            )
        lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
        start = span["start"] - 1
        end = span["end"]
        if start < 0 or end > len(lines):
            raise ValueError(f"span is outside {span['file_path']!r}")
        substring = next(
            (line.strip()[:120] for line in lines[start:end] if line.strip()),
            "",
        )
        if not substring:
            raise ValueError(f"span has no nonblank source line in {span['file_path']!r}")
        labels.append({"file_path": span["file_path"], "substring": substring})
    return labels


def question_counts(questions: list[dict[str, Any]]) -> dict[str, int]:
    answerable = sum(question.get("answerable") is True for question in questions)
    return {
        "total": len(questions),
        "answerable": answerable,
        "unanswerable": len(questions) - answerable,
    }


def build_question_set(
    repo_id: str,
    pinned_sha: str,
    questions: list[dict[str, Any]],
    *,
    reviewed_on: date | None,
    targets: str,
    review_status: str = "maintainer reviewed",
) -> dict[str, Any]:
    """Build the v2 JSON envelope and stamp each record with its review status."""

    if targets not in TARGETS:
        raise ValueError(f"unknown question targets {targets!r}")
    records = [
        {**question, "review_status": question.get("review_status", review_status)}
        for question in questions
    ]
    result: dict[str, Any] = {
        "repo_id": repo_id,
        "pinned_sha": pinned_sha,
        "dataset_version": "2.0-draft",
        "review_status": review_status,
        "counts": question_counts(records),
        "questions": records,
    }
    if reviewed_on is not None:
        result["reviewed_on"] = reviewed_on.isoformat()
    return result


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or not path.parts
        or ":" in path.parts[0]
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        return None
    return value


def _span_source_text(
    snapshot_root: Path,
    relative_path: str,
    line_start: int,
    line_end: int,
) -> tuple[str | None, int | None]:
    root = snapshot_root.resolve()
    source = (root / Path(*PurePosixPath(relative_path).parts)).resolve()
    if not source.is_relative_to(root) or not source.is_file():
        return None, None
    lines = source.read_text(encoding="utf-8", errors="replace").splitlines()
    if line_end > len(lines):
        return None, len(lines)
    return "\n".join(lines[line_start - 1 : line_end]), len(lines)


def _mined_source_files(
    question_id: str,
    source_ref: object,
    snapshot_root: Path | None,
    errors: list[str],
) -> set[str]:
    if not isinstance(source_ref, dict) or any(
        not isinstance(source_ref.get(field), int)
        or isinstance(source_ref.get(field), bool)
        or source_ref[field] < 1
        for field in ("issue", "pr")
    ):
        errors.append(f"{question_id}: mined question needs issue and pr source_ref")
        return set()
    changed_files = source_ref.get("changed_source_files")
    if not isinstance(changed_files, list) or not changed_files:
        errors.append(
            f"{question_id}: mined question needs changed non-test source files in source_ref"
        )
        return set()
    valid_files: set[str] = set()
    for value in changed_files:
        relative_path = _safe_relative_path(value)
        if relative_path is None or not is_source_python_path(relative_path):
            errors.append(f"{question_id}: source_ref contains a non-source or test file")
            continue
        valid_files.add(relative_path)
        if snapshot_root is not None:
            source_path = snapshot_root.joinpath(*PurePosixPath(relative_path).parts)
            if not source_path.is_file():
                errors.append(f"{question_id}: changed source file is absent at pinned SHA")
    return valid_files


def _contains_copied_chunk_phrase(question: str, source_text: str, *, size: int = 8) -> bool:
    question_tokens = re.findall(r"[a-z0-9_]+", question.casefold())
    source_tokens = re.findall(r"[a-z0-9_]+", source_text.casefold())
    if not source_tokens:
        return False
    size = min(size, len(source_tokens))
    if len(question_tokens) < size:
        return False
    question_phrases = {
        tuple(question_tokens[index : index + size])
        for index in range(len(question_tokens) - size + 1)
    }
    return any(
        tuple(source_tokens[index : index + size]) in question_phrases
        for index in range(len(source_tokens) - size + 1)
    )


def validate_question_set(
    data: dict[str, Any],
    *,
    repo_id: str | None = None,
    pinned_sha: str | None = None,
    snapshot_root: Path | None = None,
    targets: str = "full",
    required_review_status: str = "maintainer reviewed",
) -> list[str]:
    """Return all v2 schema, quota, leakage, secret, and span validation errors."""

    errors: list[str] = []
    target = TARGETS.get(targets)
    if target is None:
        return [f"unknown question targets {targets!r}"]
    if not isinstance(data, dict):
        return ["question set must be an object"]
    if not isinstance(data.get("repo_id"), str) or not data["repo_id"]:
        errors.append("repo_id must be a non-empty string")
    elif repo_id is not None and data["repo_id"] != repo_id:
        errors.append("repo_id does not match candidate")
    set_sha = data.get("pinned_sha")
    if not isinstance(set_sha, str) or not set_sha:
        errors.append("pinned_sha must be a non-empty string")
    elif pinned_sha is not None and set_sha != pinned_sha:
        errors.append("pinned_sha does not match candidate")
    if data.get("dataset_version") != "2.0-draft":
        errors.append("dataset_version must be '2.0-draft'")
    if data.get("review_status") != required_review_status:
        errors.append(f"review_status must be {required_review_status!r}")
    reviewed_on = data.get("reviewed_on")
    if required_review_status == LLM_ONLY_REVIEW_STATUS:
        if "reviewed_on" in data:
            errors.append("reviewed_on is not valid for LLM-only question sets")
        if snapshot_root is None:
            errors.append("snapshot_root is required for LLM-only question validation")
    elif not isinstance(reviewed_on, str):
        errors.append("reviewed_on must be an ISO date")
    else:
        try:
            date.fromisoformat(reviewed_on)
        except ValueError:
            errors.append("reviewed_on must be an ISO date")

    questions = data.get("questions")
    if not isinstance(questions, list):
        return errors + ["questions must be a list"]
    if any(not isinstance(question, dict) for question in questions):
        return errors + ["every question must be an object"]
    ids = [question.get("id") for question in questions]
    if any(not isinstance(item, str) or not item for item in ids):
        errors.append("every question id must be a non-empty string")
    elif len(ids) != len(set(ids)):
        errors.append("question ids must be unique")

    answerable_questions = [
        question for question in questions if question.get("answerable") is True
    ]
    unanswerable_questions = [
        question for question in questions if question.get("answerable") is False
    ]
    if len(answerable_questions) != target["answerable"]:
        errors.append(
            f"expected {target['answerable']} answerable questions; "
            f"found {len(answerable_questions)}"
        )
    if len(unanswerable_questions) != target["unanswerable"]:
        errors.append(
            f"expected {target['unanswerable']} unanswerable questions; "
            f"found {len(unanswerable_questions)}"
        )
    if data.get("counts") != question_counts(questions):
        errors.append("header counts do not match questions")

    type_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    kind_counts: Counter[str] = Counter()
    file_questions: dict[str, set[str]] = {}
    max_type_count = int(target["answerable"] * 0.4)

    for question in questions:
        question_id = str(question.get("id") or "<missing>")
        text = question.get("question")
        if not isinstance(text, str) or not text.strip():
            errors.append(f"{question_id}: question must be non-empty")
            text = ""
        if question.get("review_status") != required_review_status:
            errors.append(f"{question_id}: review_status must be {required_review_status!r}")
        if required_review_status == LLM_ONLY_REVIEW_STATUS:
            if "reviewed" in question:
                errors.append(f"{question_id}: reviewed is invalid for LLM-only questions")
        elif question.get("reviewed") is not True:
            errors.append(f"{question_id}: reviewed must be true")
        source = question.get("source")
        source_valid = isinstance(source, str) and source in SOURCES
        if not source_valid:
            errors.append(f"{question_id}: source must be mined, drafted, or human")
        evidence = question.get("evidence")
        if not isinstance(evidence, str) or len(evidence) > 300:
            errors.append(f"{question_id}: evidence must be text of at most 300 characters")
            evidence = ""
        for field, value in (("question", text), ("evidence", evidence)):
            secret = find_secret(value)
            if secret:
                errors.append(f"{question_id}: secret pattern {secret} in {field}")

        source_files: set[str] = set()
        if source == "mined":
            source_files = _mined_source_files(
                question_id, question.get("source_ref"), snapshot_root, errors
            )
        elif "source_ref" in question:
            errors.append(f"{question_id}: source_ref is reserved for mined questions")
        if source == "drafted" and (
            not isinstance(question.get("drafting_model"), str)
            or not question["drafting_model"].strip()
        ):
            errors.append(f"{question_id}: drafted question needs drafting_model")

        answerable = question.get("answerable")
        if not isinstance(answerable, bool):
            errors.append(f"{question_id}: answerable must be boolean")
            continue
        if answerable:
            if source_valid:
                source_counts[source] += 1
            question_type = question.get("type")
            question_type_valid = (
                isinstance(question_type, str) and question_type in ANSWERABLE_TYPES
            )
            if not question_type_valid:
                errors.append(f"{question_id}: invalid answerable type")
            else:
                type_counts[question_type] += 1
            if question_type_valid and question.get("category") != legacy_category(question):
                errors.append(f"{question_id}: legacy category does not match v2 labels")

            spans = question.get("relevant_spans")
            labels = question.get("relevant")
            if not isinstance(spans, list) or not spans:
                errors.append(f"{question_id}: answerable question needs relevant_spans")
                spans = []
            if not isinstance(labels, list) or len(labels) != len(spans):
                errors.append(f"{question_id}: relevant labels must match relevant_spans")
                labels = []
            seen_paths: set[str] = set()
            for index, span in enumerate(spans):
                if not isinstance(span, dict):
                    errors.append(f"{question_id}: relevant span must be an object")
                    continue
                relative_path = _safe_relative_path(span.get("file_path"))
                line_start = span.get("line_start")
                line_end = span.get("line_end")
                if relative_path is None:
                    errors.append(f"{question_id}: relevant span has an unsafe file_path")
                    continue
                if (
                    not isinstance(line_start, int)
                    or isinstance(line_start, bool)
                    or not isinstance(line_end, int)
                    or isinstance(line_end, bool)
                    or line_start < 1
                    or line_end < line_start
                ):
                    errors.append(f"{question_id}: relevant span line range is invalid")
                    continue
                seen_paths.add(relative_path)
                if not is_source_python_path(relative_path):
                    errors.append(f"{question_id}: gold file must be a non-test source file")
                if source == "mined" and relative_path not in source_files:
                    errors.append(f"{question_id}: gold file was not changed by the closing PR")
                basename = PurePosixPath(relative_path).name.casefold()
                if relative_path.casefold() in text.casefold() or basename in text.casefold():
                    errors.append(f"{question_id}: question contains gold path or basename")
                file_questions.setdefault(relative_path, set()).add(question_id)
                if index < len(labels):
                    label = labels[index]
                    if (
                        not isinstance(label, dict)
                        or label.get("file_path") != relative_path
                        or not isinstance(label.get("substring"), str)
                        or not label["substring"]
                    ):
                        errors.append(f"{question_id}: relevant label is invalid")
                if snapshot_root is not None:
                    span_text, line_count = _span_source_text(
                        snapshot_root, relative_path, line_start, line_end
                    )
                    if span_text is None:
                        if line_count is None:
                            errors.append(
                                f"{question_id}: missing or unsafe span file {relative_path}"
                            )
                        else:
                            errors.append(f"{question_id}: span exceeds {relative_path} line count")
                    else:
                        secret = find_secret(span_text)
                        if secret:
                            errors.append(
                                f"{question_id}: secret pattern {secret} in evidence span"
                            )
                        if source == "drafted" and _contains_copied_chunk_phrase(text, span_text):
                            errors.append(f"{question_id}: drafted question copies gold-chunk text")
            for label in labels:
                if isinstance(label, dict) and _safe_relative_path(label.get("file_path")) is None:
                    errors.append(f"{question_id}: relevant label has an unsafe file_path")
            if seen_paths:
                for path in seen_paths:
                    file_questions.setdefault(path, set()).add(question_id)
        else:
            kind = question.get("kind")
            kind_valid = isinstance(kind, str) and kind in UNANSWERABLE_KINDS
            if not kind_valid:
                errors.append(f"{question_id}: invalid unanswerable kind")
            else:
                kind_counts[kind] += 1
            if kind_valid and question.get("category") != legacy_category(question):
                errors.append(f"{question_id}: legacy category does not match v2 labels")
            if question.get("relevant") or question.get("relevant_spans"):
                errors.append(f"{question_id}: unanswerable question must not have gold labels")
            absence_check = question.get("absence_check")
            if not isinstance(absence_check, dict):
                errors.append(f"{question_id}: absence_check must be an object")
            else:
                terms = absence_check.get("terms")
                if (
                    not isinstance(terms, list)
                    or not terms
                    or any(not isinstance(term, str) or not term.strip() for term in terms)
                ):
                    errors.append(f"{question_id}: absence_check terms must be non-empty")
                hits = absence_check.get("hits")
                if not isinstance(hits, int) or isinstance(hits, bool) or hits != 0:
                    errors.append(f"{question_id}: absence_check hits must be zero")
                if absence_check.get("pinned_sha") != set_sha:
                    errors.append(f"{question_id}: absence_check pinned_sha does not match")
                if required_review_status == LLM_ONLY_REVIEW_STATUS:
                    search_command = absence_check.get("search_command")
                    if (
                        not isinstance(search_command, str)
                        or not search_command.strip()
                        or not isinstance(terms, list)
                        or set_sha not in search_command
                        or any(
                            term not in search_command for term in terms if isinstance(term, str)
                        )
                    ):
                        errors.append(
                            f"{question_id}: absence_check needs the recorded pinned search command"
                        )

    missing_types = ANSWERABLE_TYPES.difference(type_counts)
    if missing_types:
        errors.append(f"answerable types missing from set: {', '.join(sorted(missing_types))}")
    for question_type, count in type_counts.items():
        if count > max_type_count:
            errors.append(
                f"answerable type {question_type!r} exceeds 40% ({count} > {max_type_count})"
            )
    minimum_source = int(target["minimum_source"])
    if source_counts["mined"] < minimum_source:
        errors.append(f"at least {minimum_source} mined answerable questions are required")
    if source_counts["drafted"] + source_counts["human"] < minimum_source:
        errors.append(
            f"at least {minimum_source} drafted-or-human answerable questions are required"
        )
    if kind_counts != Counter(target["unanswerable_kinds"]):
        errors.append("unanswerable kind counts do not match target quotas")
    for path, question_ids in file_questions.items():
        if len(question_ids) > 3:
            errors.append(f"more than 3 questions use gold file {path!r}")
    return errors
