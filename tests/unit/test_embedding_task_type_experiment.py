from __future__ import annotations

from pathlib import Path

import pytest

from evaluation.embedding_task_type import (
    DOCUMENT_TASK_TYPE,
    QUERY_TASK_TYPE,
    collect_embedding_inputs,
    compare_guard_decisions,
    embedding_cache_key,
    evaluate_task_type_rules,
    paired_mrr_statistics,
    read_cached_vector,
    render_results,
    summarize_method,
)
from evaluation.retrieval_eval import _explicit_development_questions


def _metrics(
    *,
    mrr: float,
    hit_at_5: int = 10,
    recall_denominator: int | None = 3,
    recall_hits: int | None = 2,
) -> dict[str, int | float | None]:
    return {
        "mrr": mrr,
        "hit_at_5_successes": hit_at_5,
        "test_source_recall_denominator": recall_denominator,
        "test_source_recall_hits": recall_hits,
    }


def _decision(
    *,
    candidate_mrr: float = 0.2,
    lower_bound: float = 0.01,
    candidate_hits: int = 10,
    guard_regressions: int = 0,
    recall_denominator: int | None = 3,
    candidate_recall_hits: int | None = 1,
) -> dict[str, object]:
    control = _metrics(
        mrr=0.1,
        recall_denominator=recall_denominator,
        recall_hits=2 if recall_denominator else None,
    )
    candidate = _metrics(
        mrr=candidate_mrr,
        hit_at_5=candidate_hits,
        recall_denominator=recall_denominator,
        recall_hits=candidate_recall_hits,
    )
    bootstrap = {"bootstrap_95_percentile_interval": [lower_bound, 0.2]}
    return evaluate_task_type_rules(
        control,
        candidate,
        {"repo": control},
        {"repo": candidate},
        {"repo": {"regressed": guard_regressions}},
        bootstrap,
    )


def test_embedding_cache_key_separates_task_type_and_experiment_version() -> None:
    document_key = embedding_cache_key("same text", DOCUMENT_TASK_TYPE)
    query_key = embedding_cache_key("same text", QUERY_TASK_TYPE)

    assert document_key != query_key
    assert document_key == embedding_cache_key("same text", DOCUMENT_TASK_TYPE)
    assert len(document_key) == 64


def test_collect_embedding_inputs_uses_only_supplied_development_rows() -> None:
    inputs = collect_embedding_inputs(
        {
            "repo": {
                "chunks": [
                    {"content": "source chunk"},
                    {"content": "source chunk"},
                    {"content": "another chunk"},
                ]
            }
        },
        {
            "repo": [
                {"id": "development-only-1", "question": "first dev query"},
                {"id": "development-only-2", "question": "second dev query"},
            ]
        },
    )

    assert set(inputs.document_texts) == {"source chunk", "another chunk"}
    assert set(inputs.query_texts) == {"first dev query", "second dev query"}


def test_offline_runner_rejects_non_development_question_records() -> None:
    entry = {"splits": {"development": ["dev-1"], "held_out": ["held-1"]}}

    selected = _explicit_development_questions(
        entry,
        "development",
        [{"id": "dev-1", "question": "development"}],
    )
    assert selected == [{"id": "dev-1", "question": "development"}]

    with pytest.raises(ValueError, match="unique development rows"):
        _explicit_development_questions(
            entry,
            "development",
            [{"id": "held-1", "question": "held-out"}],
        )
    with pytest.raises(ValueError, match="only for development"):
        _explicit_development_questions(
            entry,
            "held_out",
            [{"id": "dev-1", "question": "development"}],
        )


def test_read_cached_vector_requires_768_finite_values(tmp_path: Path) -> None:
    valid_path = tmp_path / "valid.json"
    valid_path.write_text("[" + ",".join(["0"] * 768) + "]", encoding="utf-8")
    assert len(read_cached_vector(valid_path)) == 768

    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text("[NaN]", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid cached embedding vector"):
        read_cached_vector(invalid_path)


def test_summarize_method_reports_span_ranks_and_test_source_denominator() -> None:
    questions = [
        {
            "category": "direct",
            "relevant": [{"file_path": "src/module.py", "substring": "target"}],
            "relevant_spans": [
                {"file_path": "src/module.py", "line_start": 4, "line_end": 4}
            ],
        }
    ]
    results = [
        {
            "file_path": "src/module.py",
            "line_start": 1,
            "line_end": 5,
            "content": "target",
            "vector_score": 0.1,
        }
    ]

    metrics = summarize_method([(questions[0], results)])

    assert metrics["answerable_questions"] == 1
    assert metrics["hit_at_1_successes"] == 1
    assert metrics["mrr"] == 1.0
    assert metrics["span_mrr"] == 1.0
    assert metrics["test_source_recall_denominator"] == 0
    assert metrics["reciprocal_ranks"] == [1.0]


def test_bootstrap_is_reproducible_with_registered_seed() -> None:
    control = [1.0, 0.0, 0.5]
    candidate = [0.5, 1.0, 0.5]

    first = paired_mrr_statistics(control, candidate, resamples=100)
    second = paired_mrr_statistics(control, candidate, resamples=100)

    assert first == second
    assert first["bootstrap_seed"] == 20261031
    assert first["bootstrap_resamples"] == 100
    assert first["sign_test"] == {
        "positive": 1,
        "negative": 1,
        "ties": 1,
        "two_sided_p_value": 1.0,
    }


def test_guard_comparison_reports_only_development_ordinals() -> None:
    questions = [
        {"id": "dev-a", "category": "direct"},
        {"id": "dev-b", "category": "unanswerable_near"},
        {"id": "dev-c", "category": "unanswerable_far"},
    ]
    control = {
        "dev-b": [{"vector_score": 0.8}],
        "dev-c": [{"vector_score": 0.1}],
    }
    candidate = {
        "dev-b": [{"vector_score": 0.1}],
        "dev-c": [{"vector_score": 0.8}],
    }

    comparison = compare_guard_decisions(questions, control, candidate)

    assert comparison == {
        "unanswerable_questions": 2,
        "unchanged": 0,
        "improved": 1,
        "regressed": 1,
        "changed_development_ordinals": [2, 3],
    }


def test_registered_decision_requires_every_evaluable_safeguard() -> None:
    assert _decision()["qualifies_for_retention"] is True
    assert _decision(candidate_mrr=0.12)["rules"]["R1"] == "fail"
    assert _decision(lower_bound=0)["rules"]["R2"] == "fail"
    assert _decision(candidate_hits=9)["rules"]["R3"] == "fail"
    assert _decision(guard_regressions=1)["rules"]["R4"] == "fail"
    no_test_evidence = _decision(recall_denominator=0, candidate_recall_hits=None)
    assert no_test_evidence["rules"]["R5"] == "not-evaluable"
    assert no_test_evidence["qualifies_for_retention"] is False
    assert _decision(candidate_recall_hits=0)["rules"]["R5"] == "fail"


def test_rendered_report_contains_no_question_ids_or_text() -> None:
    method = {
        "answerable_questions": 1,
        "hit_at_1_successes": 1,
        "hit_at_3_successes": 1,
        "hit_at_5_successes": 1,
        "mrr": 1.0,
        "span_mrr": 1.0,
        "test_top5_chunks": 0,
        "top5_chunks": 5,
        "test_top5_share": 0.0,
        "test_source_recall_denominator": 0,
        "test_source_recall_hits": 0,
        "test_source_recall": None,
        "test_precision_overlaps": 0,
        "answerable_test_top5_chunks": 0,
        "test_precision": None,
    }
    report = {
        "per_repository": {
            "repo": {"control": method, "candidate": method}
        },
        "pooled": {"control": method, "candidate": method},
        "bootstrap": {
            "mrr_difference": 0.0,
            "bootstrap_95_percentile_interval": [0.0, 0.0],
            "bootstrap_seed": 20261031,
            "bootstrap_resamples": 10000,
            "sign_test": {
                "positive": 0,
                "negative": 0,
                "ties": 1,
                "two_sided_p_value": 1.0,
            },
        },
        "guard_by_repository": {
            "repo": {
                "unanswerable_questions": 1,
                "unchanged": 1,
                "improved": 0,
                "regressed": 0,
                "changed_development_ordinals": [],
            }
        },
        "decision": {
            "rules": {f"R{index}": "pass" for index in range(1, 6)},
            "outcome": "Keep the control.",
        },
        "held_out_question_id": "HELDOUT-ID-MUST-NOT-APPEAR",
        "question_text": "HELDOUT-TEXT-MUST-NOT-APPEAR",
    }

    rendered = render_results(report)

    assert "HELDOUT-ID-MUST-NOT-APPEAR" not in rendered
    assert "HELDOUT-TEXT-MUST-NOT-APPEAR" not in rendered
