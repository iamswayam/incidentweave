from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evaluation.gate import evaluate_gate, load_gate


def gate_config() -> dict[str, Any]:
    return {
        "baseline_report": "evaluation/repos/incidentweave/offline-baseline.json",
        "baselines": {
            label: {"hit_at_5_successes": 11, "mrr": 0.5729166666666666}
            for label in ("substring_labels", "spans")
        },
        "tolerance": {
            "hit_at_5_successes_max_drop": 0,
            "mrr_max_drop": 0.02,
        },
    }


def report(hit_successes: int = 11, mrr: float = 0.5729166666666666) -> dict[str, Any]:
    return {
        "summary": {
            label: {"hit_at_5": {"successes": hit_successes}, "mrr": mrr}
            for label in ("substring_labels", "spans")
        }
    }


def test_gate_passes_baseline_and_mrr_exact_tolerance_boundary() -> None:
    gate = gate_config()
    baseline = gate["baselines"]["substring_labels"]["mrr"]
    result = evaluate_gate(report(mrr=baseline - 0.02), gate)

    assert result["passed"]
    assert all(check["passed"] for check in result["checks"])


def test_gate_fails_hit_at_5_drop_of_one_question() -> None:
    result = evaluate_gate(report(hit_successes=10), gate_config())

    assert not result["passed"]
    assert [check for check in result["checks"] if check["metric"] == "hit_at_5_successes"]
    assert all(
        not check["passed"]
        for check in result["checks"]
        if check["metric"] == "hit_at_5_successes"
    )


def test_gate_fails_mrr_drop_beyond_tolerance() -> None:
    baseline = gate_config()["baselines"]["spans"]["mrr"]
    result = evaluate_gate(report(mrr=baseline - 0.020001), gate_config())

    assert not result["passed"]
    assert all(
        not check["passed"] for check in result["checks"] if check["metric"] == "mrr"
    )


def test_gate_passes_improvements() -> None:
    assert evaluate_gate(report(hit_successes=12, mrr=0.8), gate_config())["passed"]


def test_load_gate_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(gate_config()), encoding="utf-8")

    assert load_gate(path) == gate_config()
