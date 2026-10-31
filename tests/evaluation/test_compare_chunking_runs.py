from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from evaluation import compare_chunking_runs
from evaluation.compare_chunking_runs import compare_runs, format_report

PINNED_SOURCE = (
    "MODULE_LABEL = 1\n"
    "# FUNCTION_LABEL = 2 also appears at module scope.\n"
    "\n"
    "def target():\n"
    "    FUNCTION_LABEL = 2\n"
    "    return FUNCTION_LABEL\n"
)


def _record(
    identifier: str,
    category: str,
    label: str | None,
    rank: int | None,
    *,
    outcome: str = "correct_labeled_context",
    enough: bool = True,
    token_count: int = 100,
    file_path: str = "src/sample.py",
) -> dict[str, Any]:
    labels = (
        [{"file_path": file_path, "substring": label}] if label else []
    )
    results = []
    if rank is not None:
        for index in range(1, rank + 1):
            is_labeled = index == rank
            results.append(
                {
                    "file_path": file_path if is_labeled else "src/other.py",
                    "line_start": 1 if label == "MODULE_LABEL = 1" else 3,
                    "line_end": (
                        1
                        if label == "MODULE_LABEL = 1"
                        else (6 if index == rank else 3)
                    ),
                    "content": label if is_labeled and label else "context",
                }
            )
    return {
        "id": identifier,
        "category": category,
        "relevant": labels,
        "labeled_rank": rank,
        "retrieval_results": results,
        "generation_trace": {"total_tokens": token_count},
        "evidence_check": {"is_sufficient": enough},
        "outcome_v2": outcome,
    }


def _write_run(
    folder: Path,
    run_id: str,
    first_pass: list[dict[str, Any]],
    second_pass: list[dict[str, Any]],
) -> None:
    folder.mkdir(parents=True)
    (folder / "report.json").write_text(
        json.dumps({"run_id": run_id, "pinned_sha": "pinned-test-sha"}),
        encoding="utf-8",
    )
    for name, records in (("pass-1", first_pass), ("pass-2", second_pass)):
        (folder / f"{name}.json").write_text(json.dumps(records), encoding="utf-8")


def _fixture_records(experiment: bool) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    q1 = _record("direct-01", "direct", "MODULE_LABEL = 1", 1, token_count=80)
    q2 = _record(
        "paraphrased-01",
        "paraphrased",
        "FUNCTION_LABEL = 2",
        2 if experiment else None,
        outcome="correct_labeled_context" if experiment else "model_abstained",
        token_count=120,
        file_path="tests/test_sample.py",
    )
    q3 = _record(
        "direct-02",
        "direct",
        "MODULE_LABEL = 1",
        None if experiment else 6,
        outcome="incomplete_or_wrong",
        token_count=100,
    )
    unanswerable = _record(
        "unanswerable_far-01",
        "unanswerable_far",
        None,
        None,
        outcome="answered_unanswerable" if experiment else "guard_true_refusal",
        enough=experiment,
        token_count=200,
    )
    pass_one = [q1, q2, q3, unanswerable]
    pass_two = [dict(record) for record in pass_one]
    pass_two[2] = {
        **pass_two[2],
        "outcome_v2": "correct_unlabeled_context" if experiment else "incomplete_or_wrong",
    }
    return pass_one, pass_two


def test_compare_synthetic_runs_reports_net_plus_one_as_inconclusive(
    tmp_path: Path,
) -> None:
    baseline_passes = _fixture_records(experiment=False)
    experiment_passes = _fixture_records(experiment=True)
    baseline_dir = tmp_path / "baseline"
    experiment_dir = tmp_path / "experiment"
    _write_run(baseline_dir, "baseline-run", *baseline_passes)
    _write_run(experiment_dir, "experiment-run", *experiment_passes)

    report = compare_runs(
        baseline_dir,
        experiment_dir,
        source_reader=lambda _sha, _path: PINNED_SOURCE,
    )

    gates = {gate["gate"]: gate for gate in report["gates"]}
    assert gates["8"]["status"] == "FAIL"
    assert "INCONCLUSIVE" in gates["8"]["evidence"]
    assert "retain baseline" in gates["8"]["evidence"]
    assert report["metrics_by_pass"]["baseline"]["pass-1"]["overall"]["hit_at_5"] == 1
    assert report["metrics_by_pass"]["experiment"]["pass-1"]["overall"]["hit_at_5"] == 2
    assert report["metrics_by_pass"]["experiment"]["pass-1"]["hit_by_function"] == {
        "hit_at_5": 1,
        "applicable_questions": 1,
        "not_applicable_module_level": 2,
    }
    assert {
        (item["pass"], item["id"])
        for item in report["outcome_v2_changes"]
    } == {
        ("pass-1", "paraphrased-01"),
        ("pass-1", "unanswerable_far-01"),
        ("pass-2", "direct-02"),
        ("pass-2", "paraphrased-01"),
        ("pass-2", "unanswerable_far-01"),
    }
    assert report["metrics_by_pass"]["experiment"]["pass-1"]["guard_false_accepts"] == 1
    experiment_metrics = report["metrics_by_pass"]["experiment"]["pass-1"]
    assert experiment_metrics["by_category"]["direct"]["mrr"] == 0.5
    assert experiment_metrics["by_category"]["paraphrased"]["hit_at_5"] == 1
    assert experiment_metrics["by_label_file_type"]["test_file"]["questions"] == 1
    assert experiment_metrics["by_label_file_type"]["test_file"]["hit_at_5"] == 1
    assert experiment_metrics["by_label_file_type"]["non_test_file"]["questions"] == 2
    assert experiment_metrics["top5_context_characters"]["per_question"][0] == {
        "id": "direct-01",
        "characters": len("MODULE_LABEL = 1"),
    }
    assert experiment_metrics["total_tokens"]["median"] == 110
    assert {
        item["id"]: item["total_tokens"]
        for item in experiment_metrics["total_tokens"]["per_question"]
    } == {
        "direct-01": 80,
        "paraphrased-01": 120,
        "direct-02": 100,
        "unanswerable_far-01": 200,
    }
    gate_four = next(gate for gate in report["gates"] if gate["gate"] == "4")
    assert gate_four["status"] == "FAIL"
    assert "unanswerable_far-01" in gate_four["evidence"]


def test_module_level_label_is_n_a_for_function_hit(tmp_path: Path) -> None:
    module_record = _record("direct-01", "direct", "MODULE_LABEL = 1", 1)
    baseline_dir = tmp_path / "baseline"
    experiment_dir = tmp_path / "experiment"
    _write_run(baseline_dir, "baseline-run", [module_record], [module_record])
    _write_run(experiment_dir, "experiment-run", [module_record], [module_record])

    report = compare_runs(
        baseline_dir,
        experiment_dir,
        source_reader=lambda _sha, _path: PINNED_SOURCE,
    )

    metrics = report["metrics_by_pass"]["experiment"]["pass-1"]["hit_by_function"]
    assert metrics == {
        "hit_at_5": 0,
        "applicable_questions": 0,
        "not_applicable_module_level": 1,
    }
    row = report["paired_questions_pass_1"][0]
    assert row["baseline_hit_by_function"] is None
    assert row["experiment_hit_by_function"] is None
    assert "n/a/n/a" in format_report(report)

    baseline_miss_dir = tmp_path / "baseline-miss"
    experiment_hit_dir = tmp_path / "experiment-hit"
    baseline_miss = _record("direct-01", "direct", "MODULE_LABEL = 1", None)
    experiment_hit = _record("direct-01", "direct", "MODULE_LABEL = 1", 1)
    _write_run(baseline_miss_dir, "baseline-miss", [baseline_miss], [baseline_miss])
    _write_run(experiment_hit_dir, "experiment-hit", [experiment_hit], [experiment_hit])
    module_only_gain = compare_runs(
        baseline_miss_dir,
        experiment_hit_dir,
        source_reader=lambda _sha, _path: PINNED_SOURCE,
    )
    gate_seven = next(gate for gate in module_only_gain["gates"] if gate["gate"] == "7")
    assert gate_seven["status"] == "PASS"


def test_cli_writes_comparison_json_next_to_experiment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    baseline_dir = tmp_path / "runs" / "baseline"
    experiment_dir = tmp_path / "runs" / "experiment"
    first_pass = [_record("direct-01", "direct", "MODULE_LABEL = 1", 1)]
    second_pass = [dict(first_pass[0])]
    _write_run(baseline_dir, "baseline-run", first_pass, second_pass)
    _write_run(experiment_dir, "experiment-run", first_pass, second_pass)
    monkeypatch.setattr(compare_chunking_runs, "RUNS_ROOT", tmp_path / "runs")
    monkeypatch.setattr(
        compare_chunking_runs,
        "read_pinned_source",
        lambda _sha, _path: PINNED_SOURCE,
    )
    monkeypatch.setattr(
        "sys.argv",
        ["compare_chunking_runs.py", str(baseline_dir), str(experiment_dir)],
    )

    compare_chunking_runs.main()

    output_path = experiment_dir / "chunking-comparison.json"
    written = json.loads(output_path.read_text(encoding="utf-8"))
    assert written["experiment_run_id"] == "experiment-run"
    assert "Gate checklist:" in capsys.readouterr().out
