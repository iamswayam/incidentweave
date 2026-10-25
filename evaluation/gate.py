"""Pure loading and evaluation for the offline retrieval regression gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

MRR_EPSILON = 1e-9


def load_gate(path: Path) -> dict[str, Any]:
    """Load the committed retrieval gate configuration."""

    return json.loads(path.read_text(encoding="utf-8"))


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
