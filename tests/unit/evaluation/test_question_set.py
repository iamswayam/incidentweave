from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from evaluation.question_set import (
    build_question_set,
    derive_relevant_labels,
    legacy_category,
    validate_question_set,
)

PINNED_SHA = "a" * 40


def _record(
    index: int,
    *,
    source: str = "mined",
    question_type: str = "direct",
    answerable: bool = True,
    kind: str = "far",
    path: str | None = None,
) -> dict[str, Any]:
    record: dict[str, Any] = {
        "id": f"Q-{index:03d}",
        "question": f"What does operation {index} return?",
        "answerable": answerable,
        "source": source,
        "reviewed": True,
        "evidence": "return value",
        "review_minutes": 5,
    }
    if answerable:
        relative = path or f"src/file_{index}.py"
        spans = [{"file_path": relative, "line_start": 1, "line_end": 2}]
        record.update(
            {
                "type": question_type,
                "category": "direct" if question_type == "direct" else "paraphrased",
                "relevant": [{"file_path": relative, "substring": "return value"}],
                "relevant_spans": spans,
            }
        )
        if source == "mined":
            record["source_ref"] = {"issue": index + 1, "pr": index + 101}
        if source == "drafted":
            record["drafting_model"] = "test-drafter"
    else:
        record.update(
            {
                "kind": kind,
                "category": "unanswerable_far" if kind == "far" else "unanswerable_near",
                "relevant": [],
                "relevant_spans": [],
                "absence_check": {
                    "terms": [f"absent_{index}"],
                    "hits": 0,
                    "pinned_sha": PINNED_SHA,
                },
            }
        )
        if source == "drafted":
            record["drafting_model"] = "test-drafter"
    return record


def _valid_set(root: Path, targets: str = "full") -> dict[str, Any]:
    answerable_count = 30 if targets == "full" else 20
    unanswerable_kinds = (
        ["far"] * 4 + ["near-miss"] * 3 + ["false-premise"] * 3
        if targets == "full"
        else ["far"] * 3 + ["near-miss"] * 3 + ["false-premise"] * 2
    )
    questions = []
    for index in range(answerable_count):
        source = "mined" if index < answerable_count // 2 else "drafted"
        question_type = (
            "direct",
            "paraphrase",
            "multi-file",
            "config-env",
            "error-message",
            "how-it-works",
        )[index % 6]
        question = _record(index, source=source, question_type=question_type)
        path = root / question["relevant_spans"][0]["file_path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("def operation():\n    return value\n", encoding="utf-8")
        questions.append(question)
    for offset, kind in enumerate(unanswerable_kinds, answerable_count):
        source = "human"
        questions.append(_record(offset, source=source, answerable=False, kind=kind))
    return build_question_set(
        "candidate",
        PINNED_SHA,
        questions,
        reviewed_on=date(2026, 11, 2),
        targets=targets,
    )


def _errors(data: dict[str, Any], root: Path | None = None, targets: str = "full") -> list[str]:
    return validate_question_set(
        data,
        repo_id="candidate",
        pinned_sha=PINNED_SHA,
        snapshot_root=root,
        targets=targets,
    )


def test_full_and_reduced_question_targets_validate(tmp_path: Path) -> None:
    full_root = tmp_path / "full"
    full = _valid_set(full_root)
    assert _errors(full, full_root) == []

    reduced_root = tmp_path / "reduced"
    reduced = _valid_set(reduced_root, "reduced")
    assert _errors(reduced, reduced_root, "reduced") == []


def test_legacy_relevance_labels_are_derived_from_reviewed_span(tmp_path: Path) -> None:
    source = tmp_path / "src" / "module.py"
    source.parent.mkdir()
    source.write_text("\n\ndef target():\n    return exact_value\n", encoding="utf-8")
    spans = [{"file_path": "src/module.py", "start": 2, "end": 4}]

    labels = derive_relevant_labels(spans, tmp_path)

    assert labels == [{"file_path": "src/module.py", "substring": "def target():"}]


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("repo_id", "other", "repo_id does not match candidate"),
        ("pinned_sha", "b" * 40, "pinned_sha does not match candidate"),
        ("dataset_version", "2.0", "dataset_version must be"),
        ("review_status", "not reviewed", "review_status must be"),
        ("reviewed_on", "not-a-date", "reviewed_on must be"),
    ],
)
def test_header_validation(tmp_path: Path, field: str, value: object, message: str) -> None:
    data = _valid_set(tmp_path)
    data[field] = value
    assert any(message in error for error in _errors(data))


def test_rejects_duplicate_ids_and_header_count_mismatch(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][1]["id"] = data["questions"][0]["id"]
    data["counts"]["answerable"] = 0
    errors = _errors(data)
    assert any("question ids must be unique" in error for error in errors)
    assert any("header counts do not match" in error for error in errors)


def test_rejects_wrong_review_and_source_and_drafting_model(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["reviewed"] = False
    data["questions"][15]["source"] = "other"
    data["questions"][16].pop("drafting_model")
    errors = _errors(data)
    assert any("reviewed must be true" in error for error in errors)
    assert any("source must be" in error for error in errors)
    assert any("drafted question needs drafting_model" in error for error in errors)


def test_rejects_question_quotas_and_source_minimums(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    answerable = data["questions"][:30]
    data["questions"] = answerable + data["questions"][30:-1]
    data["counts"] = {"total": len(data["questions"]), "answerable": 30, "unanswerable": 9}
    for question in answerable[15:]:
        question["source"] = "mined"
        question.pop("drafting_model", None)
    errors = _errors(data)
    assert any("expected 10 unanswerable" in error for error in errors)
    assert any("drafted-or-human answerable" in error for error in errors)


def test_rejects_answerable_type_above_forty_percent(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    for question in data["questions"][:13]:
        question["type"] = "direct"
        question["category"] = "direct"
    assert any("exceeds 40%" in error for error in _errors(data))


def test_rejects_more_than_three_questions_per_gold_file(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    shared = "src/shared.py"
    for question in data["questions"][:4]:
        question["relevant"] = [{"file_path": shared, "substring": "return value"}]
        question["relevant_spans"] = [{"file_path": shared, "line_start": 1, "line_end": 2}]
    assert any("more than 3 questions use gold file" in error for error in _errors(data))


def test_rejects_gold_path_leakage_and_unsafe_spans(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["question"] = "What does src/file_0.py do?"
    data["questions"][1]["relevant_spans"][0]["line_start"] = 0
    errors = _errors(data, tmp_path)
    assert any("gold path or basename" in error for error in errors)
    assert any("line range is invalid" in error for error in errors)


@pytest.mark.parametrize("unsafe_path", [".", "C:/src/module.py", "src\\module.py", "../secret.py"])
def test_rejects_unsafe_gold_paths(tmp_path: Path, unsafe_path: str) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["relevant"][0]["file_path"] = unsafe_path
    data["questions"][0]["relevant_spans"][0]["file_path"] = unsafe_path

    assert any("unsafe file_path" in error for error in _errors(data))


def test_rejects_span_outside_snapshot_and_secrets(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["evidence"] = "api_key='12345678901234567890'"
    data["questions"][1]["relevant_spans"][0]["line_end"] = 3
    errors = _errors(data, tmp_path)
    assert any("secret pattern" in error for error in errors)
    assert any("span exceeds" in error for error in errors)


def test_rejects_unanswerable_kind_counts_labels_and_absence_hits(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    first = data["questions"][30]
    first["kind"] = "unknown"
    first["relevant"] = [{"file_path": "src/x.py", "substring": "x"}]
    first["absence_check"]["hits"] = 1
    errors = _errors(data)
    assert any("invalid unanswerable kind" in error for error in errors)
    assert any("must not have gold labels" in error for error in errors)
    assert any("absence_check hits must be zero" in error for error in errors)
    assert any("kind counts do not match" in error for error in errors)


def test_rejects_invalid_mined_source_ref_and_evidence_length(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["source_ref"]["issue"] = True
    data["questions"][1]["evidence"] = "x" * 301
    errors = _errors(data)
    assert any("mined question needs issue and pr" in error for error in errors)
    assert any("evidence must be text of at most 300" in error for error in errors)


def test_legacy_category_mapping_keeps_answerability(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    assert legacy_category(data["questions"][0]) == "direct"
    assert legacy_category(data["questions"][1]) == "paraphrased"
    assert legacy_category(data["questions"][30]) == "unanswerable_far"


def test_validator_rejects_unknown_targets_and_wrong_repo(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    assert validate_question_set(data, targets="unknown") == ["unknown question targets 'unknown'"]
    assert any(
        "repo_id does not match" in error
        for error in validate_question_set(data, repo_id="other", pinned_sha=PINNED_SHA)
    )


def test_rejects_no_secret_question_and_incompatible_relevance_label(tmp_path: Path) -> None:
    data = _valid_set(tmp_path)
    data["questions"][0]["question"] = "Use token='12345678901234567890' for this."
    data["questions"][1]["relevant"][0]["file_path"] = "different.py"
    errors = _errors(data)
    assert any("secret pattern" in error for error in errors)
    assert any("relevant label is invalid" in error for error in errors)
