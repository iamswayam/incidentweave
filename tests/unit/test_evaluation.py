from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.golden import validate_golden_set, validate_index_labels
from evaluation.metrics import (
    answer_screen,
    distance_sweep,
    guard_confusion,
    hit_at_k,
    is_refused,
    is_relevant,
    mean_reciprocal_rank,
    retrieval_summary,
)


def result(file_path: str, content: str) -> dict[str, object]:
    return {"file_path": file_path, "content": content}


def test_retrieval_metrics_handle_hits_ties_and_no_hit() -> None:
    results = [
        [result("a.py", "alpha"), result("b.py", "beta")],
        [result("b.py", "beta"), result("a.py", "alpha")],
        [result("c.py", "gamma")],
    ]
    labels = [
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "a.py", "substring": "alpha"}],
        [{"file_path": "z.py", "substring": "zeta"}],
    ]

    assert hit_at_k(results, labels, 1) == 1
    assert hit_at_k(results, labels, 3) == 2
    assert mean_reciprocal_rank(results, labels) == (1 + 0.5) / 3
    assert retrieval_summary(results, labels)["hit_at_5"] == 2


def test_mrr_averages_equal_ranks_and_counts_no_hit_as_zero() -> None:
    results = [
        [result("other.py", "no"), result("target.py", "yes")],
        [result("elsewhere.py", "no"), result("target.py", "yes")],
        [result("other.py", "no")],
    ]
    labels = [[{"file_path": "target.py", "substring": "yes"}]] * 3

    assert mean_reciprocal_rank(results, labels) == pytest.approx(1 / 3)


def test_relevance_rule_is_case_insensitive_and_requires_same_file() -> None:
    labels = [{"file_path": "src/store.py", "substring": "PersistResult"}]

    assert is_relevant(result("src/store.py", "class persistresult:"), labels)
    assert not is_relevant(result("src/other.py", "class PersistResult:"), labels)


def test_guard_confusion_and_distance_sweep() -> None:
    answerable = [True, True, False, False]
    sufficient = [True, False, False, True]
    assert guard_confusion(answerable, sufficient) == {
        "true_accept": 1,
        "false_refusal": 1,
        "true_refusal": 1,
        "false_accept": 1,
    }

    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.51},
    ]
    sweep = distance_sweep(checks, [True, False], 0.016)
    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 1,
        "false_accepts": 0,
    }
    assert len(sweep) == 16
    assert sweep[-1]["vector_cutoff"] == 0.6


def test_distance_sweep_counts_false_refusals_and_false_accepts() -> None:
    checks = [
        {"best_rrf_score": 0.02, "best_vector_score": 0.31},
        {"best_rrf_score": 0.02, "best_vector_score": 0.5},
        {"best_rrf_score": 0.02, "best_vector_score": 0.35},
        {"best_rrf_score": 0.01, "best_vector_score": 0.2},
    ]
    sweep = distance_sweep(checks, [True, True, False, False], 0.016)

    assert sweep[0] == {
        "vector_cutoff": 0.3,
        "false_refusals": 2,
        "false_accepts": 0,
    }
    assert sweep[3] == {
        "vector_cutoff": 0.36,
        "false_refusals": 1,
        "false_accepts": 1,
    }
    assert sweep[10] == {
        "vector_cutoff": 0.5,
        "false_refusals": 0,
        "false_accepts": 1,
    }


def test_answer_screen_and_refusal() -> None:
    assert answer_screen("AsyncSessionLocal uses async_sessionmaker", [["sessionmaker"], ["async"]])
    assert not answer_screen("Only a database engine is described", [["sessionmaker"]])
    assert is_refused("INSUFFICIENT_EVIDENCE")
    assert is_refused(" INSUFFICIENT_EVIDENCE ")
    assert not is_refused("INSUFFICIENT_EVIDENCE", generation_latency_ms=75)
    assert not is_refused("Diagnosis: insufficient evidence")


def _valid_golden_data(snapshot_root: Path) -> dict[str, object]:
    questions = []
    for index, category in enumerate(["direct"] * 8 + ["paraphrased"] * 8):
        relative_path = f"area{index}.py"
        content = f"label phrase {index}"
        (snapshot_root / relative_path).write_text(
            f"value = {content!r}\n", encoding="utf-8"
        )
        questions.append(
            {
                "id": f"{category}-{index}",
                "category": category,
                "question": "How does this behavior work?",
                "seen_before": False,
                "relevant": [{"file_path": relative_path, "substring": content}],
                "must_mention": [["label"]],
            }
        )
    questions.extend(
        {
            "id": f"unanswerable-{index}",
            "category": "unanswerable_far" if index < 4 else "unanswerable_near",
            "question": "How is this absent feature handled?",
            "seen_before": False,
            "absent_terms": ["feature-not-present"],
        }
        for index in range(8)
    )
    return {
        "pinned_sha": "snapshot-sha",
        "review_status": "pending maintainer review",
        "counts": {
            "direct": 8,
            "paraphrased": 8,
            "unanswerable_far": 4,
            "unanswerable_near": 4,
        },
        "questions": questions,
    }


def test_golden_validation_accepts_valid_schema_and_snapshot(tmp_path: Path) -> None:
    data = _valid_golden_data(tmp_path)

    assert validate_golden_set(data, tmp_path, "snapshot-sha") == []


def test_golden_validation_rejects_duplicate_ids_invalid_category_and_counts(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[1]["id"] = questions[0]["id"]
    questions[0]["category"] = "invalid"
    data["counts"]["direct"] = 7

    errors = validate_golden_set(data, tmp_path, "other-sha")

    assert "question ids are not unique" in errors
    assert any("invalid categories" in error for error in errors)
    assert any("category counts differ" in error for error in errors)
    assert "header counts do not match the required category counts" in errors
    assert "pinned_sha does not match the exported snapshot" in errors


def test_golden_validation_rejects_missing_labels_absent_terms_and_answer_labels(
    tmp_path: Path,
) -> None:
    data = _valid_golden_data(tmp_path)
    questions = data["questions"]
    questions[0]["relevant"] = [{"file_path": "missing.py", "substring": "absent"}]
    questions[-1]["absent_terms"] = ["LABEL PHRASE 1"]
    questions[-2]["absent_terms"] = []
    questions[-3]["relevant"] = [{"file_path": "area0.py", "substring": "label phrase 0"}]

    errors = validate_golden_set(data, tmp_path, "snapshot-sha")

    assert any("missing label file" in error for error in errors)
    assert any("absent term appears" in error for error in errors)
    assert any("unanswerable_near requires absent_terms" in error for error in errors)
    assert any("unanswerable question has answer labels" in error for error in errors)


def test_index_validation_requires_a_reachable_chunk() -> None:
    questions = [
        {
            "id": "direct-1",
            "category": "direct",
            "relevant": [{"file_path": "source.py", "substring": "target phrase"}],
        }
    ]

    assert validate_index_labels(
        questions, [result("source.py", "contains target phrase")]
    ) == []
    assert validate_index_labels(questions, [result("source.py", "no target")]) == [
        "direct-1: no indexed chunk matches a relevance label"
    ]
