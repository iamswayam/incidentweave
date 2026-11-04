from __future__ import annotations

import math

import pytest

from evaluation.metrics import (
    auroc,
    context_precision_at_k,
    ndcg_at_k,
    recall_at_k,
    refusal_precision_recall,
)
from evaluation.scorecard import build_scorecard
from evaluation.stats import stratified_bootstrap_interval


def _chunk(path: str, start: int, end: int) -> dict[str, object]:
    return {"file_path": path, "line_start": start, "line_end": end}


def test_ndcg_is_one_for_perfect_ranking_and_matches_hand_calculation() -> None:
    spans = [
        {"file_path": "target.py", "line_start": 1, "line_end": 4},
        {"file_path": "target.py", "line_start": 8, "line_end": 10},
    ]
    relevant_first = _chunk("target.py", 1, 4)
    relevant_second = _chunk("target.py", 8, 10)
    irrelevant = _chunk("other.py", 1, 3)
    corpus = [relevant_first, relevant_second, irrelevant]

    assert ndcg_at_k([relevant_first, relevant_second], spans, corpus, 2) == 1.0
    expected = (1 / math.log2(3)) / (1 + 1 / math.log2(3))
    assert ndcg_at_k([irrelevant, relevant_first], spans, corpus, 2) == pytest.approx(
        expected
    )


def test_recall_and_context_precision_use_span_overlap() -> None:
    spans = [
        {"file_path": "target.py", "line_start": 1, "line_end": 4},
        {"file_path": "target.py", "line_start": 8, "line_end": 10},
    ]
    first = _chunk("target.py", 2, 3)
    irrelevant = _chunk("other.py", 1, 3)

    assert recall_at_k([first, irrelevant], spans, 2) == 0.5
    assert context_precision_at_k([first, irrelevant], spans, 2) == 0.5
    assert context_precision_at_k([], spans, 5) == 0.0


def test_auroc_awards_half_credit_for_ties() -> None:
    assert auroc([0.5, 0.5], [False, True]) == 0.5
    assert auroc([0.1, 0.2, 0.8, 0.9], [False, False, True, True]) == 1.0


def test_refusal_precision_and_recall() -> None:
    result = refusal_precision_recall(
        [True, True, False, False],
        [False, True, True, False],
    )
    assert result == {
        "true_positive": 1,
        "false_positive": 1,
        "false_negative": 1,
        "precision": 0.5,
        "recall": 0.5,
    }


def test_stratified_bootstrap_is_deterministic_for_fixed_seed() -> None:
    strata = {"a": [1.0, 2.0], "b": [3.0, 4.0]}

    def mean(values: list[float]) -> float:
        return sum(values) / len(values)

    first = stratified_bootstrap_interval(strata, mean, seed=20261031, resamples=100)
    second = stratified_bootstrap_interval(strata, mean, seed=20261031, resamples=100)

    assert first == second


def test_scorecard_refuses_held_out_exports() -> None:
    with pytest.raises(ValueError, match="refuses any split other than development"):
        build_scorecard(
            {"metadata": {"split": "held_out"}},
        )
