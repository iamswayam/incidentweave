"""Golden-set loading and validation."""

from __future__ import annotations

import json
import re
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

VALID_CATEGORIES = {"direct", "paraphrased", "unanswerable_far", "unanswerable_near"}
EXPECTED_COUNTS = {
    "direct": 8,
    "paraphrased": 8,
    "unanswerable_far": 4,
    "unanswerable_near": 4,
}
PRIOR_QUESTION_MARKERS = (
    "async sessions",
    "ceo's car",
    "violin tuning",
    "quartz comet",
    "health endpoint",
)


def load_golden_set(path: Path) -> dict[str, Any]:
    """Load the JSON golden set without external dependencies."""

    return json.loads(path.read_text(encoding="utf-8"))


def _code_identifiers(value: str) -> set[str]:
    identifiers = set()
    for token in re.findall(r"[A-Za-z][A-Za-z0-9_]*", value):
        if "_" in token or re.search(r"[a-z][A-Z]|[A-Z][a-z]+[A-Z]", token):
            identifiers.add(token.casefold())
    return identifiers


def validate_golden_set(
    data: dict[str, Any],
    snapshot_root: Path,
    expected_sha: str | None = None,
) -> list[str]:
    """Return schema, coverage, source-label, and leakage validation errors."""

    errors: list[str] = []
    if not isinstance(data.get("pinned_sha"), str) or not data["pinned_sha"]:
        errors.append("pinned_sha must be a non-empty string")
    elif expected_sha is not None and data["pinned_sha"] != expected_sha:
        errors.append("pinned_sha does not match the exported snapshot")
    if data.get("review_status") != "pending maintainer review":
        errors.append("review_status must be 'pending maintainer review'")

    questions = data.get("questions")
    if not isinstance(questions, list):
        return ["questions must be a list"]

    if any(not isinstance(question, dict) for question in questions):
        return errors + ["every question must be an object"]

    ids = [question.get("id") for question in questions]
    if len(ids) != len(set(ids)):
        errors.append("question ids are not unique")
    if any(not isinstance(question_id, str) or not question_id for question_id in ids):
        errors.append("every question id must be a non-empty string")

    categories = [question.get("category") for question in questions]
    if set(categories) - VALID_CATEGORIES:
        errors.append(f"invalid categories: {sorted(set(categories) - VALID_CATEGORIES)}")
    observed_counts = Counter(categories)
    if observed_counts != Counter(EXPECTED_COUNTS):
        errors.append(f"category counts differ: {observed_counts}")
    if data.get("counts") != EXPECTED_COUNTS:
        errors.append("header counts do not match the required category counts")

    prior_questions = 0
    labels_per_file: Counter[str] = Counter()
    seen_before_count = 0

    for question in questions:
        question_id = question.get("id", "<missing>")
        category = question.get("category")
        question_text = question.get("question")
        if not isinstance(question_text, str) or not question_text.strip():
            errors.append(f"{question_id}: missing question")
            question_text = ""
        if not isinstance(question.get("seen_before"), bool):
            errors.append(f"{question_id}: seen_before must be boolean")
        elif question["seen_before"]:
            seen_before_count += 1
        if any(marker in question_text.casefold() for marker in PRIOR_QUESTION_MARKERS):
            prior_questions += 1
            if question.get("seen_before") is not True:
                errors.append(f"{question_id}: prior-phase question must set seen_before")

        if category in {"direct", "paraphrased"}:
            labels = question.get("relevant")
            must_mention = question.get("must_mention")
            if not isinstance(labels, list) or not labels:
                errors.append(f"{question_id}: missing relevant labels")
            if not isinstance(must_mention, list) or not must_mention:
                errors.append(f"{question_id}: missing must_mention")
            for label in labels or []:
                if not isinstance(label, dict):
                    errors.append(f"{question_id}: relevance label must be an object")
                    continue
                relative_path = label.get("file_path")
                substring = label.get("substring")
                if not isinstance(relative_path, str) or not relative_path:
                    errors.append(f"{question_id}: label file_path must be a non-empty string")
                    continue
                if not isinstance(substring, str) or not substring:
                    errors.append(f"{question_id}: label substring must be a non-empty string")
                    continue
                file_path = (snapshot_root / relative_path).resolve()
                if not file_path.is_relative_to(snapshot_root.resolve()):
                    errors.append(f"{question_id}: label path escapes the snapshot")
                    continue
                if not file_path.is_file():
                    errors.append(f"{question_id}: missing label file {relative_path}")
                    continue
                labels_per_file[relative_path] += 1
                content = file_path.read_text(encoding="utf-8", errors="replace")
                if substring.casefold() not in content.casefold():
                    errors.append(f"{question_id}: missing label substring")
                if category == "paraphrased":
                    identifiers = _code_identifiers(
                        file_path.stem + " " + substring + " " + content
                    )
                    question_identifiers = _code_identifiers(question_text)
                    leaked = sorted(identifiers & question_identifiers)
                    if leaked:
                        errors.append(
                            f"{question_id}: contains source identifier(s): {', '.join(leaked)}"
                        )
                    if file_path.stem.casefold() in question_text.casefold():
                        errors.append(f"{question_id}: contains file name stem")
            if isinstance(must_mention, list) and any(
                not isinstance(group, list)
                or not group
                or any(not isinstance(term, str) or not term for term in group)
                for group in must_mention
            ):
                errors.append(f"{question_id}: must_mention must contain non-empty string lists")
        else:
            if question.get("relevant") or question.get("must_mention"):
                errors.append(f"{question_id}: unanswerable question has answer labels")
            absent_terms = question.get("absent_terms", [])
            if category == "unanswerable_near" and not absent_terms:
                errors.append(f"{question_id}: unanswerable_near requires absent_terms")
            if not isinstance(absent_terms, list) or any(
                not isinstance(term, str) or not term for term in absent_terms
            ):
                errors.append(f"{question_id}: absent_terms must be non-empty strings")
                continue
            for term in absent_terms:
                for source in snapshot_root.rglob("*.py"):
                    source_text = source.read_text(
                        encoding="utf-8", errors="replace"
                    ).casefold()
                    if term.casefold() in source_text:
                        errors.append(f"{question_id}: absent term appears in {source}")
                        break

    if prior_questions > 4:
        errors.append("more than four questions repeat known prior-phase prompts")
    if seen_before_count > 4:
        errors.append("more than four questions are marked seen_before")
    if len(labels_per_file) < 6:
        errors.append("answerable questions must span at least six labeled files")
    for relative_path, count in labels_per_file.items():
        if count > 3:
            errors.append(f"more than three answerable questions label {relative_path}")

    return errors


def validate_index_labels(
    questions: Sequence[Mapping[str, Any]],
    chunks: Sequence[Mapping[str, object]],
) -> list[str]:
    """Ensure every answerable question has a reachable indexed label."""

    from .metrics import is_relevant

    errors = []
    for question in questions:
        if question.get("category") not in {"direct", "paraphrased"}:
            continue
        labels = question.get("relevant", [])
        if not any(is_relevant(chunk, labels) for chunk in chunks):
            question_id = question.get("id", "<missing>")
            errors.append(
                f"{question_id}: no indexed chunk matches a relevance label"
            )
    return errors
