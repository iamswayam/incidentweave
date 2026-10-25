"""Deterministic stratified question assignments for repository evaluations."""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

SPLIT_CHOICES = ("development", "held_out", "smoke", "all")


def _is_answerable(question: dict[str, Any]) -> bool:
    category = question.get("category")
    if isinstance(category, str):
        return not category.startswith("unanswerable")
    return bool(question.get("answerable"))


def _allocate_quotas(
    groups: dict[str | None, list[str]],
    count: int,
    rng: random.Random,
) -> dict[str | None, int]:
    total = sum(len(ids) for ids in groups.values())
    if not 0 <= count <= total:
        raise ValueError(f"requested {count} questions from a group of {total}")
    if total == 0:
        return {category: 0 for category in groups}

    quotas: dict[str | None, int] = {}
    remainders: list[tuple[float, float, str | None]] = []
    for category, ids in groups.items():
        exact = count * len(ids) / total
        quotas[category] = int(exact)
        remainders.append((exact - int(exact), rng.random(), category))
    remaining = count - sum(quotas.values())
    for _fraction, _tie_break, category in sorted(
        remainders, key=lambda item: (-item[0], item[1])
    )[:remaining]:
        quotas[category] += 1
    return quotas


def _stratified_selection(
    questions: Sequence[dict[str, Any]],
    answerable_count: int,
    unanswerable_count: int,
    rng: random.Random,
) -> set[str]:
    selected: set[str] = set()
    for answerable, target in (
        (True, answerable_count),
        (False, unanswerable_count),
    ):
        groups: dict[str | None, list[str]] = defaultdict(list)
        for question in questions:
            if _is_answerable(question) is answerable:
                category = question.get("category")
                groups[category if isinstance(category, str) else None].append(
                    str(question["id"])
                )
        quotas = _allocate_quotas(groups, target, rng)
        for category, ids in groups.items():
            shuffled_ids = list(ids)
            rng.shuffle(shuffled_ids)
            selected.update(shuffled_ids[: quotas[category]])
    return selected


def assign_splits(
    questions: Sequence[dict[str, Any]],
    seed: int,
    *,
    development_answerable: int = 11,
    development_unanswerable: int = 5,
    smoke_answerable: int = 5,
    smoke_unanswerable: int = 3,
) -> dict[str, list[str]]:
    """Assign stratified development, held-out, and development-only smoke IDs."""

    rng = random.Random(seed)
    development_ids = _stratified_selection(
        questions,
        development_answerable,
        development_unanswerable,
        rng,
    )
    question_ids = [str(question["id"]) for question in questions]
    if len(question_ids) != len(set(question_ids)):
        raise ValueError("question ids must be unique")
    if not development_ids <= set(question_ids):
        raise ValueError("development assignment contains unknown question ids")

    development_questions = [
        question for question in questions if str(question["id"]) in development_ids
    ]
    smoke_ids = _stratified_selection(
        development_questions,
        smoke_answerable,
        smoke_unanswerable,
        rng,
    )
    return {
        "development": [
            question_id for question_id in question_ids if question_id in development_ids
        ],
        "held_out": [
            question_id for question_id in question_ids if question_id not in development_ids
        ],
        "smoke": [
            question_id for question_id in question_ids if question_id in smoke_ids
        ],
    }
