"""Metrics and preregistered decision rules for test-file ranking variants."""

from __future__ import annotations

import random
from collections.abc import Mapping, Sequence
from typing import Any

from app.investigation.guard import evaluate_evidence_sufficiency
from evaluation.metrics import (
    first_relevant_rank,
    first_relevant_span_rank,
    is_relevant_span,
)
from evaluation.stats import exact_sign_test
from evaluation.test_file_variants import (
    control_top_five,
    downweight_test_chunks,
    exclude_test_chunks,
)
from evaluation.test_files import is_test_path

BOOTSTRAP_SEED = 20261031
BOOTSTRAP_RESAMPLES = 10_000
TOP_K = 5
ANSWERABLE_CATEGORIES = {"direct", "paraphrased"}


def _selected_results(
    question: Mapping[str, Any],
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> Sequence[Mapping[str, Any]]:
    question_id = question.get("id")
    if not isinstance(question_id, str) or question_id not in rankings:
        raise ValueError("Every selected development question needs a ranking")
    return rankings[question_id][:TOP_K]


def _answerable(question: Mapping[str, Any]) -> bool:
    return question.get("category") in ANSWERABLE_CATEGORIES


def summarize_method(
    questions: Sequence[Mapping[str, Any]],
    rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Summarize answerable retrieval quality and test-chunk exposure."""

    ranks: list[int | None] = []
    span_ranks: list[int | None] = []
    span_labels_available = True
    test_source_denominator = 0
    test_source_hits = 0
    test_chunk_count = 0
    test_chunk_overlap_count = 0
    top5_test_count = 0
    top5_result_count = 0

    for question in questions:
        results = _selected_results(question, rankings)
        test_results = [
            result
            for result in results
            if is_test_path(str(result.get("file_path") or ""))
        ]
        top5_test_count += len(test_results)
        top5_result_count += len(results)
        if not _answerable(question):
            continue

        labels = question.get("relevant", [])
        if not isinstance(labels, list):
            raise ValueError("Answerable questions need substring relevance labels")
        ranks.append(first_relevant_rank(results, labels))

        spans = question.get("relevant_spans")
        if not isinstance(spans, list):
            span_labels_available = False
            spans = []
        span_ranks.append(first_relevant_span_rank(results, spans))

        test_spans = [
            span
            for span in spans
            if isinstance(span, Mapping)
            and isinstance(span.get("file_path"), str)
            and is_test_path(span["file_path"])
        ]
        if test_spans:
            test_source_denominator += 1
            if first_relevant_span_rank(results, test_spans) is not None:
                test_source_hits += 1
        test_chunk_count += len(test_results)
        test_chunk_overlap_count += sum(
            is_relevant_span(result, test_spans) for result in test_results
        )

    question_count = len(ranks)
    mrr = (
        sum(1 / rank if rank is not None else 0.0 for rank in ranks) / question_count
        if question_count
        else 0.0
    )
    spans_mrr = (
        sum(
            1 / rank if rank is not None else 0.0 for rank in span_ranks
        )
        / question_count
        if span_labels_available and question_count
        else None
    )
    return {
        "answerable_questions": question_count,
        "hit_at_1_successes": sum(rank is not None and rank <= 1 for rank in ranks),
        "hit_at_3_successes": sum(rank is not None and rank <= 3 for rank in ranks),
        "hit_at_5_successes": sum(rank is not None and rank <= 5 for rank in ranks),
        "mrr": mrr,
        "spans_mrr": spans_mrr,
        "spans_mrr_status": (
            "available" if spans_mrr is not None else "not available"
        ),
        "test_top5_chunks": top5_test_count,
        "top5_chunks": top5_result_count,
        "test_top5_share": (
            top5_test_count / top5_result_count if top5_result_count else 0.0
        ),
        "answerable_test_top5_chunks": test_chunk_count,
        "test_precision": (
            test_chunk_overlap_count / test_chunk_count
            if test_chunk_count
            else None
        ),
        "test_precision_overlaps": test_chunk_overlap_count,
        "test_source_recall_denominator": (
            test_source_denominator if span_labels_available else None
        ),
        "test_source_recall_hits": (
            test_source_hits if span_labels_available else None
        ),
        "test_source_recall": (
            test_source_hits / test_source_denominator
            if span_labels_available and test_source_denominator
            else None
        ),
        "mrr_reciprocal_values": [
            1 / rank if rank is not None else 0.0 for rank in ranks
        ],
    }


def paired_mrr_statistics(
    control_reciprocal_ranks: Sequence[float],
    variant_reciprocal_ranks: Sequence[float],
    *,
    seed: int = BOOTSTRAP_SEED,
    resamples: int = BOOTSTRAP_RESAMPLES,
) -> dict[str, Any]:
    """Calculate the paired MRR delta, percentile bootstrap, and exact sign test."""

    if len(control_reciprocal_ranks) != len(variant_reciprocal_ranks):
        raise ValueError("Paired MRR samples must have equal lengths")
    if not control_reciprocal_ranks:
        raise ValueError("Paired MRR statistics need at least one question")
    if resamples < 1:
        raise ValueError("Bootstrap resamples must be positive")

    differences = [
        variant - control
        for control, variant in zip(
            control_reciprocal_ranks, variant_reciprocal_ranks
        )
    ]
    observed = sum(differences) / len(differences)
    rng = random.Random(seed)
    bootstrap_means = sorted(
        sum(rng.choices(differences, k=len(differences))) / len(differences)
        for _ in range(resamples)
    )

    def percentile(value: float) -> float:
        position = (len(bootstrap_means) - 1) * value
        lower = int(position)
        upper = min(lower + 1, len(bootstrap_means) - 1)
        fraction = position - lower
        return (
            bootstrap_means[lower] * (1 - fraction)
            + bootstrap_means[upper] * fraction
        )

    wins = sum(difference > 0 for difference in differences)
    losses = sum(difference < 0 for difference in differences)
    ties = len(differences) - wins - losses
    return {
        "mrr_difference": observed,
        "bootstrap_seed": seed,
        "bootstrap_resamples": resamples,
        "bootstrap_95_percentile_interval": [
            percentile(0.025),
            percentile(0.975),
        ],
        "sign_test": {
            "positive": wins,
            "negative": losses,
            "ties": ties,
            "two_sided_p_value": exact_sign_test(wins, losses),
        },
        "question_differences": differences,
    }


def compare_guard_decisions(
    questions: Sequence[Mapping[str, Any]],
    control_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
    variant_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, Any]:
    """Compare production guard decisions on unanswerable development questions."""

    unchanged = 0
    improved = 0
    regressed = 0
    changed_ordinals: list[int] = []
    unanswerable_ordinal = 0
    for development_ordinal, question in enumerate(questions, start=1):
        if _answerable(question):
            continue
        unanswerable_ordinal += 1
        control = evaluate_evidence_sufficiency(
            _selected_results(question, control_rankings)
        )["is_sufficient"]
        variant = evaluate_evidence_sufficiency(
            _selected_results(question, variant_rankings)
        )["is_sufficient"]
        if not isinstance(control, bool) or not isinstance(variant, bool):
            raise ValueError("Production guard must return a boolean decision")
        if control == variant:
            unchanged += 1
        else:
            changed_ordinals.append(development_ordinal)
            if control and not variant:
                improved += 1
            else:
                regressed += 1
    return {
        "unanswerable_questions": unanswerable_ordinal,
        "unchanged": unchanged,
        "improved": improved,
        "regressed": regressed,
        "changed_development_ordinals": changed_ordinals,
    }


def summarize_control_guard(
    questions: Sequence[Mapping[str, Any]],
    control_rankings: Mapping[str, Sequence[Mapping[str, Any]]],
) -> dict[str, int]:
    """Count production guard decisions over unanswerable development questions."""

    sufficient = 0
    insufficient = 0
    for question in questions:
        if _answerable(question):
            continue
        decision = evaluate_evidence_sufficiency(
            _selected_results(question, control_rankings)
        )["is_sufficient"]
        if not isinstance(decision, bool):
            raise ValueError("Production guard must return a boolean decision")
        sufficient += decision
        insufficient += not decision
    return {
        "unanswerable_questions": sufficient + insufficient,
        "sufficient": sufficient,
        "insufficient": insufficient,
    }


def evaluate_variant_rules(
    variant: str,
    control_pooled: Mapping[str, Any],
    variant_pooled: Mapping[str, Any],
    control_by_repository: Mapping[str, Mapping[str, Any]],
    variant_by_repository: Mapping[str, Mapping[str, Any]],
    guard_by_repository: Mapping[str, Mapping[str, Any]],
    bootstrap: Mapping[str, Any],
    *,
    test_source_recall_denominator: int | None,
    control_test_source_recall_hits: int | None,
    variant_test_source_recall_hits: int | None,
    registered_test_evidence_stratum_size: int,
) -> dict[str, Any]:
    """Evaluate every registered rule without treating an unevaluable rule as a pass."""

    if variant not in {"V1", "V2"}:
        raise ValueError("Variant must be V1 or V2")
    difference = float(variant_pooled["mrr"]) - float(control_pooled["mrr"])
    interval = bootstrap["bootstrap_95_percentile_interval"]
    rules: dict[str, str] = {
        "R1": "pass" if difference >= 0.03 else "fail",
        "R2": "pass" if float(interval[0]) > 0 else "fail",
        "R3": (
            "pass"
            if all(
                int(variant_by_repository[repository]["hit_at_5_successes"])
                >= int(control_by_repository[repository]["hit_at_5_successes"])
                for repository in control_by_repository
            )
            else "fail"
        ),
        "R4": (
            "pass"
            if all(int(metrics["regressed"]) == 0 for metrics in guard_by_repository.values())
            else "fail"
        ),
    }
    if test_source_recall_denominator is None or test_source_recall_denominator == 0:
        rules["R5"] = "not-evaluable"
    else:
        if control_test_source_recall_hits is None or variant_test_source_recall_hits is None:
            raise ValueError("Evaluable R5 requires both recall hit counts")
        rules["R5"] = (
            "pass"
            if control_test_source_recall_hits - variant_test_source_recall_hits <= 1
            else "fail"
        )

    if variant == "V1":
        rules["R6"] = "not-evaluable"
    else:
        rules["R6"] = (
            "pass"
            if registered_test_evidence_stratum_size >= 3
            and rules["R5"] == "pass"
            and all(rules[rule] == "pass" for rule in ("R1", "R2", "R3", "R4"))
            else "fail"
        )
    required_rules = ("R1", "R2", "R3", "R4", "R5")
    if variant == "V2":
        required_rules += ("R6",)
    return {
        "rules": rules,
        "passes_all_required_rules": all(rules[rule] == "pass" for rule in required_rules),
        "mrr_difference": difference,
    }


def mechanical_decision(v1: Mapping[str, Any], v2: Mapping[str, Any]) -> str:
    """Apply the protocol's V1-first decision order and V2 R6 safeguard."""

    v1_passes = bool(v1["passes_all_required_rules"])
    v2_passes = bool(v2["passes_all_required_rules"])
    v2_r6_holds = v2["rules"]["R6"] == "pass"
    if v1_passes and v2_passes:
        return "If both variants pass, retain V1 as the milder change."
    if v1_passes:
        return "If only V1 passes, retain V1."
    if v2_passes and v2_r6_holds:
        return "V1 fails; V2 is retained under R6."
    return (
        "If V1 fails, keep the control and close the item as no change; "
        "V2 never overrides this without R6."
    )


def compare_development_variants(
    repositories: Sequence[Mapping[str, Any]],
    *,
    registered_test_evidence_stratum_size: int = 0,
) -> dict[str, Any]:
    """Score control/V1/V2, paired statistics, guard changes, and decision rules."""

    per_repository: dict[str, dict[str, Any]] = {}
    guard_comparisons: dict[str, dict[str, Any]] = {"V1": {}, "V2": {}}
    pooled_reciprocal_ranks: dict[str, list[float]] = {
        "control": [],
        "V1": [],
        "V2": [],
    }
    pooled_test_source_denominator: int | None = 0
    pooled_recall_hits: dict[str, int | None] = {"control": 0, "V1": 0, "V2": 0}
    pooled_test_exposure: dict[str, dict[str, int]] = {
        method: {
            "test_top5_chunks": 0,
            "top5_chunks": 0,
            "answerable_test_top5_chunks": 0,
            "test_precision_overlaps": 0,
        }
        for method in ("control", "V1", "V2")
    }
    for repository in repositories:
        name = str(repository["repository"])
        data = repository["_comparison_data"]
        questions = data["questions"]
        full_rankings = data["control_rankings"]
        control = {
            question_id: control_top_five(ranking)
            for question_id, ranking in full_rankings.items()
        }
        v1 = {
            question_id: downweight_test_chunks(ranking)
            for question_id, ranking in full_rankings.items()
        }
        v2 = {
            question_id: exclude_test_chunks(ranking)
            for question_id, ranking in full_rankings.items()
        }
        method_rankings = {"control": control, "V1": v1, "V2": v2}
        summaries = {
            method: summarize_method(questions, rankings)
            for method, rankings in method_rankings.items()
        }
        per_repository[name] = summaries
        control_summary = summaries["control"]
        denominator = control_summary["test_source_recall_denominator"]
        if denominator is None:
            pooled_test_source_denominator = None
        elif pooled_test_source_denominator is not None:
            pooled_test_source_denominator += denominator
        for method, summary in summaries.items():
            pooled_reciprocal_ranks[method].extend(summary["mrr_reciprocal_values"])
            for key in pooled_test_exposure[method]:
                pooled_test_exposure[method][key] += summary[key]
            hits = summary["test_source_recall_hits"]
            if hits is None:
                pooled_recall_hits[method] = None
            elif pooled_recall_hits[method] is not None:
                pooled_recall_hits[method] = int(pooled_recall_hits[method]) + hits

        for variant, rankings in (("V1", v1), ("V2", v2)):
            guard_comparisons[variant][name] = compare_guard_decisions(
                questions, control, rankings
            )

    pooled: dict[str, dict[str, Any]] = {}
    for method, reciprocal_ranks in pooled_reciprocal_ranks.items():
        question_count = len(reciprocal_ranks)
        exposure = pooled_test_exposure[method]
        span_metrics = [
            metrics[method]
            for metrics in per_repository.values()
        ]
        spans_available = all(
            summary["spans_mrr"] is not None for summary in span_metrics
        )
        spans_mrr = (
            sum(
                float(summary["spans_mrr"]) * int(summary["answerable_questions"])
                for summary in span_metrics
            )
            / question_count
            if spans_available and question_count
            else None
        )
        pooled[method] = {
            "answerable_questions": question_count,
            "mrr": (
                sum(reciprocal_ranks) / question_count if question_count else 0.0
            ),
            "hit_at_1_successes": sum(value == 1 for value in reciprocal_ranks),
            "hit_at_3_successes": sum(value >= 1 / 3 for value in reciprocal_ranks),
            "hit_at_5_successes": sum(value >= 1 / 5 for value in reciprocal_ranks),
            "spans_mrr": spans_mrr,
            "spans_mrr_status": "available" if spans_mrr is not None else "not available",
            "test_top5_chunks": exposure["test_top5_chunks"],
            "top5_chunks": exposure["top5_chunks"],
            "test_top5_share": (
                exposure["test_top5_chunks"] / exposure["top5_chunks"]
                if exposure["top5_chunks"]
                else 0.0
            ),
            "answerable_test_top5_chunks": exposure["answerable_test_top5_chunks"],
            "test_precision_overlaps": exposure["test_precision_overlaps"],
            "test_precision": (
                exposure["test_precision_overlaps"]
                / exposure["answerable_test_top5_chunks"]
                if exposure["answerable_test_top5_chunks"]
                else None
            ),
            "test_source_recall_denominator": pooled_test_source_denominator,
            "test_source_recall_hits": pooled_recall_hits[method],
            "test_source_recall": (
                pooled_recall_hits[method] / pooled_test_source_denominator
                if pooled_test_source_denominator
                and pooled_recall_hits[method] is not None
                else None
            ),
            "mrr_reciprocal_values": reciprocal_ranks,
        }
    bootstrap_results = {
        variant: paired_mrr_statistics(
            pooled_reciprocal_ranks["control"],
            pooled_reciprocal_ranks[variant],
        )
        for variant in ("V1", "V2")
    }

    rules: dict[str, Any] = {}
    for variant in ("V1", "V2"):
        variant_recall_hits = pooled_recall_hits[variant]
        rules[variant] = evaluate_variant_rules(
            variant,
            pooled["control"],
            pooled[variant],
            {
                repository: metrics["control"]
                for repository, metrics in per_repository.items()
            },
            {
                repository: metrics[variant]
                for repository, metrics in per_repository.items()
            },
            guard_comparisons[variant],
            bootstrap_results[variant],
            test_source_recall_denominator=pooled_test_source_denominator,
            control_test_source_recall_hits=pooled_recall_hits["control"],
            variant_test_source_recall_hits=variant_recall_hits,
            registered_test_evidence_stratum_size=registered_test_evidence_stratum_size,
        )

    for metrics in pooled.values():
        metrics.pop("mrr_reciprocal_values")
    for repository_metrics in per_repository.values():
        for metrics in repository_metrics.values():
            metrics.pop("mrr_reciprocal_values")
    for metrics in bootstrap_results.values():
        metrics.pop("question_differences")

    return {
        "per_repository": per_repository,
        "pooled": pooled,
        "bootstrap": bootstrap_results,
        "guard_comparisons": guard_comparisons,
        "pooled_test_source_recall_denominator": pooled_test_source_denominator,
        "pooled_test_source_recall_hits": pooled_recall_hits,
        "rules": rules,
        "decision": mechanical_decision(rules["V1"], rules["V2"]),
    }
