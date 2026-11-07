from __future__ import annotations

import math
from pathlib import Path

import pytest

import evaluation.scorecard as scorecard_module
from evaluation.golden import load_golden_set
from evaluation.manifest import load_manifest, questions_for_split, sha256_file
from evaluation.metrics import (
    auroc,
    context_precision_at_k,
    ndcg_at_k,
    recall_at_k,
    refusal_precision_recall,
)
from evaluation.scorecard import build_scorecard, ranked_chunks_for_view
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
    assert ndcg_at_k([irrelevant, relevant_first], spans, corpus, 2) == pytest.approx(expected)
    assert (
        ndcg_at_k(
            [relevant_first],
            spans,
            [relevant_first, relevant_first],
            2,
        )
        == 1.0
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


def test_deep_only_metric_cannot_use_production_view() -> None:
    production_only = {"ranked_chunks_limit5": [_chunk("a.py", 1, 5)]}

    assert ranked_chunks_for_view(production_only, "production")
    with pytest.raises(ValueError, match="does not contain the deep ranking view"):
        ranked_chunks_for_view(production_only, "deep")


def test_scorecard_assigns_metrics_to_registered_views(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).resolve().parents[3]
    manifest_path = root / "evaluation" / "manifest.json"
    manifest = load_manifest(manifest_path, root=root)
    repositories = []
    for entry in sorted(manifest["repositories"], key=lambda item: item["id"]):
        question_data = load_golden_set(root / entry["questions"]["path"])
        questions = questions_for_split(entry, question_data["questions"], "development")
        rows = []
        for question in questions:
            relevant = question.get("relevant_spans", [])
            relevant_span = relevant[0] if relevant else None
            relevant_chunk = (
                _chunk(
                    relevant_span["file_path"],
                    relevant_span["line_start"],
                    relevant_span["line_end"],
                )
                if relevant_span
                else _chunk("irrelevant.py", 1, 5)
            )
            deep_chunks = [relevant_chunk]
            production_chunks = [_chunk("irrelevant.py", 1, 5)]
            category = question["category"]
            answerable = not category.startswith("unanswerable")
            distance = 0.2 if answerable else 0.7
            for chunk in (production_chunks[0], deep_chunks[0]):
                chunk["vector_distance"] = distance
                chunk["chunk_id"] = (
                    f"{chunk['file_path']}:{chunk['line_start']}-{chunk['line_end']}"
                )
            rows.append(
                {
                    "id": question["id"],
                    "repository": entry["id"],
                    "category": category,
                    "ranked_chunks_limit5": production_chunks,
                    "ranked_chunks_limit20": deep_chunks,
                    "best_vector_distance": distance,
                    "guard_refused": not answerable,
                }
            )
        repositories.append({"id": entry["id"], "questions": rows})
    export = {
        "metadata": {
            "dataset_version": "v1",
            "repository_ids": ["batch-processing-service", "incidentweave", "lifeos"],
            "split": "development",
            "retrieval_limits": {"production": 5, "deep": 20},
            "guard_view": "production",
            "guard_threshold": 0.5,
            "git_commit": "test-commit",
            "manifest_sha256": sha256_file(manifest_path),
        },
        "repositories": repositories,
    }

    def wilson(successes: int, n: int, *, view: str) -> dict[str, object]:
        return {
            "successes": successes,
            "n": n,
            "value": successes / n if n else 0.0,
            "view": view,
        }

    def bootstrap(
        rows_by_repo: dict[str, list[dict[str, object]]],
        field: str,
        repo_ids: list[str],
        *,
        view: str,
    ) -> dict[str, object]:
        values = [
            float(row[field])
            for repo_id in repo_ids
            for row in rows_by_repo[repo_id]
            if field in row
        ]
        return {
            "value": sum(values) / len(values) if values else 0.0,
            "view": view,
        }

    monkeypatch.setattr(scorecard_module, "_wilson", wilson)
    monkeypatch.setattr(scorecard_module, "_bootstrap_mean", bootstrap)
    monkeypatch.setattr(scorecard_module, "_auroc_metric", lambda *args, view: {"view": view})
    monkeypatch.setattr(scorecard_module, "_threshold_sweep", lambda rows: [])
    scorecard = build_scorecard(export, manifest_path=manifest_path, root=root)
    production = scorecard["pooled"]["retrieval"]["production"]
    deep = scorecard["pooled"]["retrieval"]["deep"]
    assert production["hit_at_5"]["value"] == 0
    assert production["hit_at_5"]["view"] == "production"
    assert production["ndcg_at_5"]["value"] == 0
    assert production["ndcg_at_5"]["view"] == "production"
    assert production["context_precision_at_5"]["view"] == "production"
    assert deep["hit_at_20"]["value"] == 1
    assert deep["hit_at_20"]["view"] == "deep"
    assert deep["ndcg_at_10"]["value"] > 0
    assert deep["ndcg_at_10"]["view"] == "deep"
    assert deep["recall_at_20"]["view"] == "deep"
    assert scorecard["pooled"]["guard"]["view"] == "production"
