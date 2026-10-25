"""Pure loading and evaluation for the offline retrieval regression gate."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from evaluation.stats import wilson_interval

MRR_EPSILON = 1e-9


def load_gate(path: Path) -> dict[str, Any]:
    """Load the committed retrieval gate configuration."""

    try:
        gate = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Cannot load retrieval gate {path}: {exc}") from exc
    if not isinstance(gate, dict):
        raise ValueError(f"Retrieval gate {path} must contain a JSON object")
    if not isinstance(gate.get("baseline_report"), str) or not gate["baseline_report"]:
        raise ValueError(f"Retrieval gate {path} needs baseline_report")
    baselines = gate.get("baselines")
    tolerances = gate.get("tolerance")
    if not isinstance(baselines, dict) or not isinstance(tolerances, dict):
        raise ValueError(f"Retrieval gate {path} needs baselines and tolerance objects")
    for label_type in ("substring_labels", "spans"):
        baseline = baselines.get(label_type)
        if not isinstance(baseline, dict):
            raise ValueError(f"Retrieval gate {path} lacks {label_type} baseline")
        successes = baseline.get("hit_at_5_successes")
        mrr = baseline.get("mrr")
        if (
            not isinstance(successes, (int, float))
            or isinstance(successes, bool)
            or not math.isfinite(successes)
            or successes < 0
        ):
            raise ValueError(f"Retrieval gate {path} has invalid {label_type} Hit@5 baseline")
        if (
            not isinstance(mrr, (int, float))
            or isinstance(mrr, bool)
            or not math.isfinite(mrr)
            or not 0 <= mrr <= 1
        ):
            raise ValueError(f"Retrieval gate {path} has invalid {label_type} MRR baseline")
    for key in ("hit_at_5_successes_max_drop", "mrr_max_drop"):
        value = tolerances.get(key)
        if (
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(f"Retrieval gate {path} has invalid tolerance {key}")
    return gate


def evaluate_gate(report: dict[str, Any], gate: dict[str, Any]) -> dict[str, Any]:
    """Compare report Hit@5 and MRR values with configured allowed minimums."""

    checks: list[dict[str, Any]] = []
    tolerances = gate["tolerance"]
    for label_type in ("substring_labels", "spans"):
        baseline = gate["baselines"][label_type]
        observed = report["summary"][label_type]
        for metric, tolerance_key in (
            ("hit_at_5_successes", "hit_at_5_successes_max_drop"),
            ("mrr", "mrr_max_drop"),
        ):
            baseline_value = baseline[metric]
            observed_value = (
                observed["hit_at_5"]["successes"]
                if metric == "hit_at_5_successes"
                else observed["mrr"]
            )
            allowed_min = baseline_value - tolerances[tolerance_key]
            passed = (
                observed_value >= allowed_min
                if metric == "hit_at_5_successes"
                else observed_value + MRR_EPSILON >= allowed_min
            )
            checks.append(
                {
                    "label_type": label_type,
                    "metric": metric,
                    "baseline": baseline_value,
                    "observed": observed_value,
                    "allowed_min": allowed_min,
                    "passed": passed,
                }
            )
    return {"passed": all(check["passed"] for check in checks), "checks": checks}


def evaluate_split_gate(
    report: dict[str, Any],
    gate: dict[str, Any],
    *,
    split: str,
    full_baseline_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Apply a repository baseline to a selected split without changing full-set gates."""

    if split not in {"development", "held_out"}:
        return evaluate_gate(report, gate)
    if not isinstance(full_baseline_report, dict):
        raise ValueError(f"A full baseline report is required for the {split} split")

    scaled_gate = json.loads(json.dumps(gate))
    for label_type in ("substring_labels", "spans"):
        baseline_summary = full_baseline_report["summary"][label_type]
        selected_count = report["summary"][label_type]["count"]
        baseline_count = baseline_summary["count"]
        if baseline_count <= 0:
            raise ValueError(f"Full baseline for {label_type} has no answerable questions")
        scaled_gate["baselines"][label_type]["hit_at_5_successes"] = (
            baseline_summary["hit_at_5"]["successes"] * selected_count / baseline_count
        )
        scaled_gate["baselines"][label_type]["mrr"] = baseline_summary["mrr"]
    return evaluate_gate(report, scaled_gate)


def pooled_report(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """Pool selected repositories' question records and calculate Wilson metrics."""

    questions = [
        {
            **question,
            "repo_id": report.get("metadata", {}).get("repo_id", "unknown"),
        }
        for report in reports
        for question in report["questions"]
        if question["category"] in {"direct", "paraphrased"}
    ]
    summary: dict[str, Any] = {}
    for label_type, rank_key in (
        ("substring_labels", "label_rank"),
        ("spans", "span_rank"),
    ):
        ranked = [question[rank_key] for question in questions]
        metrics: dict[str, Any] = {"count": len(ranked)}
        for cutoff in (1, 3, 5):
            successes = sum(rank is not None and rank <= cutoff for rank in ranked)
            low, high = wilson_interval(successes, len(ranked))
            metrics[f"hit_at_{cutoff}"] = {
                "successes": successes,
                "rate": successes / len(ranked) if ranked else 0.0,
                "wilson_95": [low, high],
            }
        metrics["mrr"] = (
            sum(1 / rank if rank else 0.0 for rank in ranked) / len(ranked)
            if ranked
            else 0.0
        )
        summary[label_type] = metrics
    return {"questions": questions, "summary": summary}
