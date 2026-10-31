from __future__ import annotations

import asyncio
from argparse import Namespace
from pathlib import Path
from typing import Any

import pytest

from evaluation.chunk_experiments import resolve_split
from evaluation.gate import pooled_report
from scripts import check_retrieval_gate


def _gate_config() -> dict[str, Any]:
    return {
        "baseline_report": "baseline.json",
        "baselines": {
            label: {"hit_at_5_successes": 3, "mrr": 0.34}
            for label in ("substring_labels", "spans")
        },
        "tolerance": {
            "hit_at_5_successes_max_drop": 0,
            "mrr_max_drop": 0.02,
        },
    }


def _repo(repo_id: str, root: Path) -> dict[str, Any]:
    resources = {}
    for field in (
        "questions",
        "fixture",
        "full_gate",
        "full_baseline",
        "smoke_baseline",
        "smoke_gate",
    ):
        path = root / f"{repo_id}-{field}.json"
        path.write_text("{}", encoding="utf-8")
        resources[field] = {"path": path.name, "sha256": "synthetic"}
    return {
        "id": repo_id,
        "questions": resources["questions"],
        "fixture": resources["fixture"],
        "full_gate": resources["full_gate"],
        "full_baseline": resources["full_baseline"],
        "smoke_baseline": resources["smoke_baseline"],
        "smoke_gate": resources["smoke_gate"],
    }


def _report(
    *,
    hit_successes: int = 3,
    mrr: float = 0.34,
    repo_id: str,
) -> dict[str, Any]:
    ranks = [1, 2, 5, None, None]
    if hit_successes < 3:
        ranks[2] = None
    if hit_successes > 3:
        ranks[3] = 4
    if mrr != 0.34:
        ranks = [1, 2, None, None, None]
    answerable = [
        {
            "id": f"{repo_id}-q{index}",
            "category": "direct",
            "label_rank": rank,
            "span_rank": rank,
        }
        for index, rank in enumerate(ranks)
    ]
    unanswerable = [
        {
            "id": f"{repo_id}-u{index}",
            "category": "unanswerable_far",
            "label_rank": None,
            "span_rank": None,
        }
        for index in range(3)
    ]
    return {
        "metadata": {"repo_id": repo_id, "split": "smoke"},
        "questions": answerable + unanswerable,
        "summary": {
            label: {
                "count": len(ranks),
                "hit_at_5": {"successes": hit_successes},
                "mrr": mrr,
            }
            for label in ("substring_labels", "spans")
        },
    }


def _setup_gate(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    reports: dict[str, dict[str, Any] | Exception],
) -> Namespace:
    manifest_path = tmp_path / "evaluation" / "manifest.json"
    manifest_path.parent.mkdir(parents=True)
    repositories = [_repo(repo_id, tmp_path) for repo_id in reports]
    manifest = {"repositories": repositories}
    monkeypatch.setattr(check_retrieval_gate, "load_manifest", lambda *_args, **_kwargs: manifest)
    monkeypatch.setattr(check_retrieval_gate, "load_gate", lambda _path: _gate_config())

    async def fake_run_offline_retrieval(
        *,
        repo_id: str,
        **_kwargs: Any,
    ) -> dict[str, Any]:
        result = reports[repo_id]
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(
        check_retrieval_gate,
        "run_offline_retrieval",
        fake_run_offline_retrieval,
    )
    return Namespace(
        manifest=manifest_path,
        repo=None,
        split="smoke",
        limit=5,
        out=None,
    )


def test_manifest_gate_prints_per_repo_and_pooled_tables(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _setup_gate(
        monkeypatch,
        tmp_path,
        {"repo-a": _report(repo_id="repo-a"), "repo-b": _report(repo_id="repo-b")},
    )

    assert asyncio.run(check_retrieval_gate._run(args)) == 0
    output = capsys.readouterr().out
    assert "Per-repository gate:" in output
    assert "repo-a" in output
    assert "repo-b" in output
    assert "Pooled retrieval metrics:" in output
    assert "10" in output
    assert "Seconds" in output


def test_manifest_gate_fails_when_one_repository_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args = _setup_gate(
        monkeypatch,
        tmp_path,
        {
            "repo-a": _report(repo_id="repo-a"),
            "repo-b": _report(hit_successes=2, mrr=0.2, repo_id="repo-b"),
        },
    )

    assert asyncio.run(check_retrieval_gate._run(args)) == 1


def test_manifest_gate_fails_when_one_repository_is_missing(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    args = _setup_gate(
        monkeypatch,
        tmp_path,
        {
            "repo-a": _report(repo_id="repo-a"),
            "repo-b": FileNotFoundError("fixture missing"),
        },
    )

    assert asyncio.run(check_retrieval_gate._run(args)) == 1
    output = capsys.readouterr().out
    assert "repo-b" in output
    assert "fixture missing" in output
    assert "Pooled results: NOT COMPUTED" in output


def test_manifest_gate_report_does_not_rewrite_gate_or_baseline_inputs(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args = _setup_gate(
        monkeypatch,
        tmp_path,
        {"repo-a": _report(repo_id="repo-a")},
    )
    entry = check_retrieval_gate.load_manifest().get("repositories", [])[0]
    protected = [
        tmp_path / entry[field]["path"]
        for field in ("full_gate", "full_baseline", "smoke_baseline", "smoke_gate")
    ]
    original_contents = [path.read_text(encoding="utf-8") for path in protected]
    args.out = tmp_path / "report.json"

    assert asyncio.run(check_retrieval_gate._run(args)) == 0
    assert args.out.is_file()
    assert [path.read_text(encoding="utf-8") for path in protected] == original_contents


def test_manifest_gate_refuses_report_path_over_manifest_input(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    args = _setup_gate(
        monkeypatch,
        tmp_path,
        {"repo-a": _report(repo_id="repo-a")},
    )
    entry = check_retrieval_gate.load_manifest().get("repositories", [])[0]
    baseline = tmp_path / entry["smoke_baseline"]["path"]
    original_contents = baseline.read_text(encoding="utf-8")
    args.out = baseline

    with pytest.raises(ValueError, match="cannot overwrite a manifest input"):
        asyncio.run(check_retrieval_gate._run(args))

    assert baseline.read_text(encoding="utf-8") == original_contents


def test_held_out_selection_requires_explicit_confirmation() -> None:
    with pytest.raises(ValueError, match="confirm-frozen-heldout"):
        resolve_split("held_out")


def test_pooled_report_preserves_incidentweave_full_set_metrics() -> None:
    ranks = [1] * 8 + [2] + [3] * 2 + [None] * 5
    questions = [
        {
            "id": f"q{index}",
            "category": "direct",
            "label_rank": rank,
            "span_rank": rank,
        }
        for index, rank in enumerate(ranks)
    ]
    report = {
        "questions": questions,
        "summary": {},
    }

    pooled = pooled_report([report])

    for label in ("substring_labels", "spans"):
        assert pooled["summary"][label]["hit_at_5"]["successes"] == 11
        assert pooled["summary"][label]["count"] == 16
        assert pooled["summary"][label]["mrr"] == pytest.approx(0.572917, abs=1e-6)
