from __future__ import annotations

import json
from collections import Counter

from evaluation.manifest import MANIFEST_PATH, load_manifest, manifest_root
from evaluation.splits import assign_splits


def synthetic_questions() -> list[dict[str, str]]:
    questions = []
    for category, count in (
        ("direct", 8),
        ("paraphrased", 8),
        ("unanswerable_far", 4),
        ("unanswerable_near", 4),
    ):
        questions.extend(
            {"id": f"{category}-{index:02}", "category": category}
            for index in range(1, count + 1)
        )
    return questions


def test_split_regeneration_is_deterministic_and_stratified() -> None:
    questions = synthetic_questions()

    first = assign_splits(questions, 20261025)
    second = assign_splits(questions, 20261025)

    assert first == second
    assert len(first["development"]) == 16
    assert len(first["held_out"]) == 8
    assert len(first["smoke"]) == 8
    assert set(first["development"]) | set(first["held_out"]) == {
        question["id"] for question in questions
    }
    assert not set(first["development"]) & set(first["held_out"])
    assert set(first["smoke"]) <= set(first["development"])
    by_id = {question["id"]: question["category"] for question in questions}
    counts = Counter(
        by_id[question_id].startswith("unanswerable")
        for question_id in first["development"]
    )
    assert counts == {False: 11, True: 5}


def test_committed_incidentweave_splits_regenerate() -> None:
    manifest = load_manifest()
    entry = manifest["repositories"][0]
    questions_path = manifest_root(MANIFEST_PATH) / entry["questions"]["path"]
    questions = json.loads(questions_path.read_text(encoding="utf-8"))["questions"]
    counts = manifest["counts"]

    regenerated = assign_splits(
        questions,
        manifest["split_seed"],
        development_answerable=counts["development_answerable"],
        development_unanswerable=counts["development_unanswerable"],
        smoke_answerable=counts["smoke_answerable"],
        smoke_unanswerable=counts["smoke_unanswerable"],
    )

    assert regenerated == entry["splits"]
