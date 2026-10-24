from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

from evaluation.gate import evaluate_gate, load_gate
from scripts import check_retrieval_gate


def gate_config() -> dict[str, Any]:
    return {
        "baseline_report": "evaluation/results/offline-baseline.json",
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


@pytest.mark.parametrize(("passes", "exit_code"), [(True, 0), (False, 1)])
def test_check_script_exit_codes_and_protected_files(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    passes: bool,
    exit_code: int,
) -> None:
    gate_path = tmp_path / "gate.json"
    baseline_path = tmp_path / "baseline.json"
    gate_path.write_text("gate contents", encoding="utf-8")
    baseline_path.write_text("baseline contents", encoding="utf-8")
    monkeypatch.setattr(check_retrieval_gate, "GATE_PATH", gate_path)
    monkeypatch.setattr(check_retrieval_gate, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(
        check_retrieval_gate,
        "load_gate",
        lambda _path: gate_config(),
    )

    async def fake_evaluation() -> dict[str, Any]:
        return report(hit_successes=11 if passes else 10)

    monkeypatch.setattr(
        check_retrieval_gate,
        "run_offline_retrieval",
        fake_evaluation,
    )
    monkeypatch.setattr(sys, "argv", ["check_retrieval_gate"])

    assert check_retrieval_gate.main() == exit_code
    assert gate_path.read_text(encoding="utf-8") == "gate contents"
    assert baseline_path.read_text(encoding="utf-8") == "baseline contents"


@pytest.mark.parametrize("protected_name", ["gate.json", "baseline.json"])
def test_check_script_refuses_out_path_that_would_overwrite_gate_or_baseline(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    protected_name: str,
) -> None:
    gate_path = tmp_path / "gate.json"
    baseline_path = tmp_path / "baseline.json"
    gate_path.write_text("gate contents", encoding="utf-8")
    baseline_path.write_text("baseline contents", encoding="utf-8")
    monkeypatch.setattr(check_retrieval_gate, "GATE_PATH", gate_path)
    monkeypatch.setattr(check_retrieval_gate, "BASELINE_PATH", baseline_path)
    monkeypatch.setattr(check_retrieval_gate, "load_gate", lambda _path: gate_config())

    async def fake_evaluation() -> dict[str, Any]:
        return report()

    monkeypatch.setattr(
        check_retrieval_gate,
        "run_offline_retrieval",
        fake_evaluation,
    )
    output_path = gate_path if protected_name == "gate.json" else baseline_path
    monkeypatch.setattr(
        sys,
        "argv",
        ["check_retrieval_gate", "--out", str(output_path)],
    )

    with pytest.raises(ValueError, match="cannot overwrite"):
        check_retrieval_gate.main()
    assert gate_path.read_text(encoding="utf-8") == "gate contents"
    assert baseline_path.read_text(encoding="utf-8") == "baseline contents"
