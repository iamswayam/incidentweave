from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import pytest

from evaluation.question_review import (
    calculate_agreement,
    create_review_pack,
    create_second_pass,
    ingest_review_pack,
    parse_pack,
    parse_second_pass,
    render_pack,
    run_agreement,
    stratified_sample,
)

PINNED_SHA = "a" * 40


def _drafts() -> list[dict[str, Any]]:
    drafts: list[dict[str, Any]] = []
    answer_types = (
        "direct",
        "paraphrase",
        "multi-file",
        "config-env",
        "error-message",
        "how-it-works",
    )
    for index in range(20):
        source = "mined" if index < 6 else "human"
        item: dict[str, Any] = {
            "candidate_id": (f"M-{index + 1:03d}" if source == "mined" else f"D-{index + 1:03d}"),
            "source": source,
            "question": f"What does operation {index} return?",
            "type": answer_types[index % len(answer_types)],
            "gold": [{"path": f"src/file_{index}.py", "start": 1, "end": 1}],
            "evidence": f"operation_{index}",
        }
        if source == "drafted":
            item["drafting_model"] = "test-drafter"
        drafts.append(item)
    for index, kind in enumerate(
        [
            "far",
            "far",
            "far",
            "near-miss",
            "near-miss",
            "near-miss",
            "false-premise",
            "false-premise",
        ]
    ):
        drafts.append(
            {
                "candidate_id": f"D-{index + 21:03d}",
                "source": "human",
                "question": f"Does the project implement absent feature {index}?",
                "kind": kind,
                "evidence": "",
                "absence_check": {
                    "terms": [f"absent_feature_{index}"],
                    "hits": 0,
                },
            }
        )
    return drafts


def _manifest(path: Path) -> None:
    path.write_text(
        json.dumps(
            {
                "candidates": [
                    {
                        "id": "candidate",
                        "url": "https://github.com/example/candidate",
                        "pinned_sha": PINNED_SHA,
                    }
                ]
            }
        ),
        encoding="utf-8",
    )


def _complete_pack(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("Decision:\n", "Decision: accept\n")
    text = text.replace("Minutes:\n", "Minutes: 5\n")
    path.write_text(text, encoding="utf-8")


def test_pack_render_and_parse_round_trip_includes_both_question_kinds() -> None:
    items = [
        {
            "candidate_id": "M-001",
            "source": "mined",
            "answerable": True,
            "question": "What does this function return?",
            "type": "direct",
            "gold": [{"path": "src/module.py", "start": 3, "end": 5}],
            "evidence": "return value",
            "owner": "example",
            "repo": "candidate",
            "mined": {
                "issue_number": 12,
                "pr_number": 13,
                "issue_title": "Incorrect return value",
                "issue_body": "The return value is unexpected.",
            },
        },
        {
            "candidate_id": "D-001",
            "source": "human",
            "answerable": False,
            "question": "Does the library support an invented feature?",
            "kind": "far",
            "absence_check": {"terms": ["invented feature"], "hits": 0},
            "evidence": "",
            "owner": "example",
            "repo": "candidate",
        },
    ]

    text, metadata, skipped = render_pack("candidate", PINNED_SHA, items)
    reviewed = text.replace("Decision:\n", "Decision: accept\n").replace(
        "Minutes:\n", "Minutes: 4\n"
    )
    blocks = parse_pack(reviewed, require_decisions=True)

    assert skipped == 0
    assert metadata["items"]["Q-001"]["candidate_id"] == "M-001"
    assert len(blocks) == 2
    assert blocks[0]["gold"] == [{"path": "src/module.py", "start": 3, "end": 5}]
    assert blocks[0]["issue_number"] == 12
    assert blocks[1]["kind"] == "far"
    assert blocks[1]["absence_terms"] == ["invented feature"]


def test_pack_parser_reports_malformed_fields_with_line_numbers() -> None:
    text = (
        "# Header\n\n"
        "## Q-001 | answerable | human\n"
        "Question: What is this?\n"
        "Type: direct\n"
        "Gold:\n"
        "- src/module.py: 2-4\n"
        "Evidence: something\n"
        "Decision: maybe\n"
        "Minutes: five\n"
        "Notes:\n"
    )

    with pytest.raises(ValueError) as error:
        parse_pack(text, require_decisions=True)

    assert "line 7: malformed gold span" in str(error.value)
    assert "line 9: Decision must be accept or reject" in str(error.value)
    assert "line 10: Minutes must be a non-negative integer" in str(error.value)


def test_pack_parser_rejects_unknown_fields_with_line_numbers() -> None:
    text = (
        "## Q-001 | answerable | human\n"
        "Question: What is this?\n"
        "Type: direct\n"
        "Gold:\n"
        "- src/module.py : 2-4\n"
        "Evidence: something\n"
        "Typo: unexpected\n"
        "Decision: accept\n"
        "Minutes: 1\n"
        "Notes:\n"
    )

    with pytest.raises(ValueError, match="line 7: unknown review field 'Typo'"):
        parse_pack(text, require_decisions=True)


def test_pack_counts_mined_items_without_questions(tmp_path: Path) -> None:
    manifest_path = tmp_path / "manifest.json"
    _manifest(manifest_path)
    cache_dir = tmp_path / "cache" / "questions" / "candidate"
    cache_dir.mkdir(parents=True)
    (cache_dir / "mined.json").write_text(
        json.dumps(
            [
                {
                    "candidate_id": "M-001",
                    "issue_number": 12,
                    "pr_number": 13,
                    "issue_title": "Synthetic issue",
                    "issue_body": "Body",
                    "files": [],
                }
            ]
        ),
        encoding="utf-8",
    )
    (cache_dir / "drafts.json").write_text("[]", encoding="utf-8")

    pack_path, skipped = create_review_pack(
        "candidate",
        manifest_path=manifest_path,
        question_cache_root=cache_dir.parent,
    )

    assert skipped == 1
    assert "## Q-" not in pack_path.read_text(encoding="utf-8")


def test_ingest_derives_retrieval_compatible_labels_from_gold_spans(
    tmp_path: Path,
) -> None:
    manifest_path = tmp_path / "manifest.json"
    _manifest(manifest_path)
    cache_root = tmp_path / "cache" / "questions"
    cache_dir = cache_root / "candidate"
    cache_dir.mkdir(parents=True)
    drafts = _drafts()
    (cache_dir / "drafts.json").write_text(json.dumps(drafts), encoding="utf-8")
    mined = [
        {
            "candidate_id": item["candidate_id"],
            "issue_number": index + 10,
            "pr_number": index + 100,
            "issue_title": "Synthetic issue",
            "issue_body": "Synthetic issue body",
            "files": [],
        }
        for index, item in enumerate(drafts[:6])
    ]
    (cache_dir / "mined.json").write_text(json.dumps(mined), encoding="utf-8")
    pack_path, skipped = create_review_pack(
        "candidate",
        manifest_path=manifest_path,
        question_cache_root=cache_root,
    )
    assert skipped == 0
    _complete_pack(pack_path)

    snapshot_root = tmp_path / "snapshot"
    for index in range(20):
        source = snapshot_root / "src" / f"file_{index}.py"
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"operation_{index} = {index}\n", encoding="utf-8")
    report = ingest_review_pack(
        "candidate",
        targets="reduced",
        manifest_path=manifest_path,
        question_cache_root=cache_root,
        output_root=tmp_path,
        snapshot_root=snapshot_root,
        today=date(2026, 11, 2),
    )
    saved = json.loads(
        (tmp_path / "evaluation" / "repos" / "candidate" / "questions.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["accepted"] == 28
    assert saved["questions"][0]["relevant"] == [
        {"file_path": "src/file_0.py", "substring": "operation_0 = 0"}
    ]
    assert saved["questions"][0]["relevant_spans"] == [
        {"file_path": "src/file_0.py", "line_start": 1, "line_end": 1}
    ]
    assert saved["questions"][0]["category"] == "direct"
    assert saved["questions"][0]["source_ref"] == {"issue": 10, "pr": 100}


def test_second_pass_sample_is_repeatable_stratified_and_sized(tmp_path: Path) -> None:
    repository_questions = {
        repo_id: [
            {
                "id": f"{repo_id}-{index}",
                "answerable": index % 2 == 0,
                "question": f"Question {repo_id} {index}",
                "relevant_spans": [{"file_path": f"src/{repo_id}_{index}.py"}],
            }
            for index in range(40)
        ]
        for repo_id in ("alpha", "beta")
    }

    sampled = stratified_sample(repository_questions)
    repeated = stratified_sample(repository_questions)
    sample_cells = {(row["repo_id"], row["question"]["answerable"]) for row in sampled}

    assert [row["question"]["id"] for row in sampled] == [row["question"]["id"] for row in repeated]
    assert len(sampled) == 16
    assert sample_cells == {
        ("alpha", True),
        ("alpha", False),
        ("beta", True),
        ("beta", False),
    }
    output_root = tmp_path / "evaluation" / "repos"
    for repo_id, questions in repository_questions.items():
        repo_dir = output_root / repo_id
        repo_dir.mkdir(parents=True)
        (repo_dir / "questions.json").write_text(
            json.dumps(
                {
                    "repo_id": repo_id,
                    "reviewed_on": "2026-10-01",
                    "questions": questions,
                }
            ),
            encoding="utf-8",
        )
    pack_path, sample_size = create_second_pass(
        ["alpha", "beta"],
        output_root=tmp_path,
        question_cache_root=tmp_path / "cache" / "questions",
        today=date(2026, 11, 2),
    )
    blind_pack = pack_path.read_text(encoding="utf-8")
    assert sample_size == 16
    assert "alpha-" not in blind_pack
    assert "Gold files:" in blind_pack
    assert blind_pack.count("## Item ") == 16


def test_second_pass_sample_uses_twenty_percent_above_sixteen() -> None:
    repository_questions = {
        "repo": [
            {
                "id": f"Q-{index:03d}",
                "answerable": index % 2 == 0,
                "question": f"Question {index}",
                "relevant_spans": [{"file_path": f"src/file_{index}.py"}],
            }
            for index in range(100)
        ]
    }

    assert len(stratified_sample(repository_questions)) == 20


def test_second_pass_parser_reports_invalid_answers_with_line_numbers() -> None:
    text = (
        "# Blind second pass\n\n"
        "## Item 1\n\n"
        "A question\n\n"
        "Answerable: maybe\n"
        "Gold files:\n"
        "Minutes: many\n"
    )

    with pytest.raises(ValueError) as error:
        parse_second_pass(text)

    assert "line 7: Answerable must be yes or no" in str(error.value)
    assert "line 9: Minutes must be a non-negative integer" in str(error.value)


@pytest.mark.parametrize(
    ("matches", "passed"),
    [(15, True), (14, False)],
)
def test_agreement_gate_boundary_for_sixteen_items(matches: int, passed: bool) -> None:
    original = [
        {
            "question_id": f"Q-{index:03d}",
            "answerable": True,
            "gold_files": [f"src/file_{index}.py"],
        }
        for index in range(1, 17)
    ]
    reviewed = [
        {
            "item": index,
            "answerable": index <= matches,
            "gold_files": [f"src/file_{index}.py"],
        }
        for index in range(1, 17)
    ]

    result = calculate_agreement(original, reviewed)

    assert result["answerability"]["agreement"] == matches
    assert result["answerability"]["passed"] is passed
    assert result["gold_files"]["passed"] is True


def test_gold_file_agreement_requires_overlap_and_reports_exact_match() -> None:
    original = [
        {
            "question_id": "Q-001",
            "answerable": True,
            "gold_files": ["src/a.py", "src/b.py"],
        },
        {
            "question_id": "Q-002",
            "answerable": True,
            "gold_files": ["src/c.py"],
        },
    ]
    reviewed = [
        {"item": 1, "answerable": True, "gold_files": ["src/b.py", "src/extra.py"]},
        {"item": 2, "answerable": True, "gold_files": ["src/other.py"]},
    ]

    result = calculate_agreement(original, reviewed)

    assert result["gold_files"]["agreement"] == 1
    assert result["gold_files"]["total"] == 2
    assert result["gold_files_exact_descriptive"]["agreement"] == 0


def test_second_pass_refuses_until_seven_days_and_reports_effort(
    tmp_path: Path,
) -> None:
    question_root = tmp_path / "cache" / "questions"
    second_pass_dir = question_root / "second-pass"
    second_pass_dir.mkdir(parents=True)
    (second_pass_dir / "metadata.json").write_text(
        json.dumps(
            {
                "created_on": "2026-11-02",
                "sample": [
                    {
                        "repo_id": "candidate",
                        "question_id": "Q-001",
                        "answerable": True,
                        "gold_files": ["src/module.py"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (second_pass_dir / "second-pass.md").write_text(
        "# Blind second pass\n\n## Item 1\n\nQuestion\n\n"
        "Answerable: yes\nGold files:\n- src/module.py\nMinutes: 3\n",
        encoding="utf-8",
    )
    repository_dir = tmp_path / "evaluation" / "repos" / "candidate"
    repository_dir.mkdir(parents=True)
    (repository_dir / "questions.json").write_text(
        json.dumps({"reviewed_on": "2026-11-02"}),
        encoding="utf-8",
    )
    (question_root / "candidate").mkdir()
    (question_root / "candidate" / "ingest-report.json").write_text(
        json.dumps({"minutes_by_item": {"Q-001": 7, "Q-002": 9}}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="requires at least 7 days"):
        run_agreement(
            ["candidate"],
            output_root=tmp_path,
            question_cache_root=question_root,
            today=date(2026, 11, 8),
        )
    result = run_agreement(
        ["candidate"],
        output_root=tmp_path,
        question_cache_root=question_root,
        today=date(2026, 11, 9),
    )

    assert result["answerability"]["rate"] == 1
    assert result["median_first_pass_minutes"] == 8
    assert result["median_effort_passed"] is True
