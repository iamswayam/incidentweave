from __future__ import annotations

from typing import Any

from evaluation.test_file_comparison import (
    compare_development_variants,
    evaluate_variant_rules,
    mechanical_decision,
    paired_mrr_statistics,
)
from scripts.compare_test_file_variants import render_results


def _rule_result(
    variant: str,
    *,
    difference: float = 0.04,
    interval_low: float = 0.01,
    control_hit5: int = 4,
    variant_hit5: int = 4,
    guard_regressions: int = 0,
    recall_denominator: int | None = 2,
    control_recall_hits: int | None = 2,
    variant_recall_hits: int | None = 2,
    test_stratum_size: int = 0,
) -> dict[str, Any]:
    return evaluate_variant_rules(
        variant,
        {"mrr": 0.4, "hit_at_5_successes": control_hit5},
        {"mrr": 0.4 + difference, "hit_at_5_successes": variant_hit5},
        {"repo": {"hit_at_5_successes": control_hit5}},
        {"repo": {"hit_at_5_successes": variant_hit5}},
        {"repo": {"regressed": guard_regressions}},
        {"bootstrap_95_percentile_interval": [interval_low, 0.1]},
        test_source_recall_denominator=recall_denominator,
        control_test_source_recall_hits=control_recall_hits,
        variant_test_source_recall_hits=variant_recall_hits,
        registered_test_evidence_stratum_size=test_stratum_size,
    )


def test_paired_bootstrap_is_reproducible_and_sign_test_is_exact() -> None:
    first = paired_mrr_statistics([0.0, 0.5, 1.0], [0.5, 0.5, 0.5])
    second = paired_mrr_statistics([0.0, 0.5, 1.0], [0.5, 0.5, 0.5])

    assert first == second
    assert first["bootstrap_seed"] == 20261031
    assert first["bootstrap_resamples"] == 10000
    assert first["sign_test"] == {
        "positive": 1,
        "negative": 1,
        "ties": 1,
        "two_sided_p_value": 1.0,
    }


def test_rule_r1_fails_below_registered_mrr_improvement() -> None:
    result = _rule_result("V1", difference=0.0299)

    assert result["rules"]["R1"] == "fail"


def test_rule_r2_requires_bootstrap_lower_bound_above_zero() -> None:
    result = _rule_result("V1", interval_low=0.0)

    assert result["rules"]["R2"] == "fail"


def test_rule_r3_fails_when_a_repository_loses_hit_at_five() -> None:
    result = _rule_result("V1", control_hit5=4, variant_hit5=3)

    assert result["rules"]["R3"] == "fail"


def test_rule_r4_fails_on_any_guard_regression() -> None:
    result = _rule_result("V1", guard_regressions=1)

    assert result["rules"]["R4"] == "fail"


def test_rule_r5_is_not_evaluable_at_zero_denominator() -> None:
    result = _rule_result(
        "V1",
        recall_denominator=0,
        control_recall_hits=0,
        variant_recall_hits=0,
    )

    assert result["rules"]["R5"] == "not-evaluable"
    assert result["passes_all_required_rules"] is False


def test_rule_r5_passes_or_fails_by_whole_question_tolerance() -> None:
    passing = _rule_result(
        "V1",
        recall_denominator=3,
        control_recall_hits=2,
        variant_recall_hits=1,
    )
    failing = _rule_result(
        "V1",
        recall_denominator=3,
        control_recall_hits=2,
        variant_recall_hits=0,
    )

    assert passing["rules"]["R5"] == "pass"
    assert failing["rules"]["R5"] == "fail"


def test_rule_r6_gates_v2_but_does_not_apply_to_v1() -> None:
    v1 = _rule_result("V1", test_stratum_size=3)
    v2_without_stratum = _rule_result(
        "V2",
        recall_denominator=3,
        control_recall_hits=2,
        variant_recall_hits=2,
        test_stratum_size=2,
    )
    v2_with_stratum = _rule_result(
        "V2",
        recall_denominator=3,
        control_recall_hits=2,
        variant_recall_hits=2,
        test_stratum_size=3,
    )

    assert v1["rules"]["R6"] == "not-evaluable"
    assert v2_without_stratum["rules"]["R6"] == "fail"
    assert v2_with_stratum["rules"]["R6"] == "pass"
    assert v2_with_stratum["passes_all_required_rules"] is True


def test_mechanical_decision_covers_both_only_v1_and_no_change_paths() -> None:
    v1_pass = _rule_result("V1", recall_denominator=1)
    v2_pass = _rule_result(
        "V2",
        recall_denominator=3,
        control_recall_hits=2,
        variant_recall_hits=2,
        test_stratum_size=3,
    )
    v2_fail = _rule_result("V2", recall_denominator=0)
    v1_not_evaluable = _rule_result(
        "V1",
        recall_denominator=0,
        control_recall_hits=0,
        variant_recall_hits=0,
    )

    assert mechanical_decision(v1_pass, v2_pass) == (
        "If both variants pass, retain V1 as the milder change."
    )
    assert mechanical_decision(v1_pass, v2_fail) == (
        "If only V1 passes, retain V1."
    )
    assert mechanical_decision(v1_not_evaluable, v2_fail) == (
        "If V1 fails, keep the control and close the item as no change; "
        "V2 never overrides this without R6."
    )
    assert mechanical_decision(
        _rule_result("V1", difference=0.02), v2_pass
    ) == "V1 fails; V2 is retained under R6."


def test_generated_note_uses_aggregates_and_never_renders_question_ids() -> None:
    question_id = "synthetic-question-id-marker"
    questions = [
        {
            "id": question_id,
            "question": "synthetic question text",
            "category": "direct",
            "relevant": [{"file_path": "src/a.py", "substring": "needle"}],
            "relevant_spans": [
                {"file_path": "src/a.py", "line_start": 1, "line_end": 2}
            ],
        },
        {
            "id": "synthetic-unanswerable-marker",
            "category": "unanswerable_near",
            "relevant": [],
            "relevant_spans": [],
        },
    ]
    ranking = {
        question_id: [
            {
                "file_path": "src/a.py",
                "content": "needle",
                "line_start": 1,
                "line_end": 2,
                "rrf_score": 0.02,
                "vector_score": 0.2,
                "vector_rank": 1,
                "fulltext_rank": 1,
            }
        ],
        "synthetic-unanswerable-marker": [
            {
                "file_path": "src/b.py",
                "content": "other",
                "line_start": 3,
                "line_end": 4,
                "rrf_score": 0.01,
                "vector_score": 0.8,
                "vector_rank": 2,
                "fulltext_rank": 2,
            }
        ],
    }
    repository = {
        "repository": "synthetic-repo",
        "_comparison_data": {
            "questions": questions,
            "control_rankings": ranking,
            "fixture_chunks": [],
        },
    }
    repository_comparison = compare_development_variants([repository])
    note = render_results([repository], repository_comparison)

    assert question_id not in note
    assert "synthetic-unanswerable-marker" not in note
    assert "synthetic question text" not in note
