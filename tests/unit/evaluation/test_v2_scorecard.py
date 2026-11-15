from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import evaluation.retrieval_eval as retrieval_eval
import evaluation.scorecard as scorecard_module
from evaluation.manifest import (
    V2_DEVELOPMENT_REPOSITORIES,
    load_v2_development_entries,
    load_v2_development_questions,
    sha256_file,
)


def _questions(repo_id: str) -> list[dict[str, Any]]:
    questions = []
    for index in range(40):
        if index < 30:
            category = "direct" if index < 15 else "paraphrased"
            spans = [{"file_path": "src/example.py", "line_start": 1, "line_end": 2}]
        else:
            category = "unanswerable_far" if index < 34 else "unanswerable_near"
            kind = "far" if index < 34 else ("near-miss" if index < 37 else "false-premise")
            spans = []
        questions.append(
            {
                "id": f"{repo_id}-{index:02}",
                "category": category,
                "question": "synthetic development question",
                "relevant_spans": spans,
                **({"kind": kind} if index >= 30 else {}),
            }
        )
    return questions


def _entries() -> dict[str, dict[str, Any]]:
    entries = {}
    for repo_id in V2_DEVELOPMENT_REPOSITORIES:
        question_ids = [question["id"] for question in _questions(repo_id)]
        entries[repo_id] = {
            "id": repo_id,
            "role": "development",
            "dataset_version": "2.0",
            "pinned_sha": f"{repo_id}-sha",
            "questions": {"path": f"{repo_id}/questions.json"},
            "fixture": {"path": f"{repo_id}/fixture.json.gz"},
            "splits": {
                "development": question_ids,
                "held_out": [],
                "smoke": [],
            },
        }
    return entries


def _export(
    manifest_path: Path,
    questions_by_repo: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    return {
        "metadata": {
            "dataset_version": "v2",
            "repository_ids": list(V2_DEVELOPMENT_REPOSITORIES),
            "split": "development",
            "retrieval_limits": {"production": 5, "deep": 20},
            "guard_view": "production",
            "guard_threshold": 0.5,
            "git_commit": "test-commit",
            "manifest_sha256": sha256_file(manifest_path),
        },
        "repositories": [
            {
                "id": repo_id,
                "questions": [
                    {
                        "id": question["id"],
                        "repository": repo_id,
                        "category": question["category"],
                        "ranked_chunks_limit5": [],
                        "ranked_chunks_limit20": [],
                        "best_vector_distance": None,
                        "guard_refused": True,
                    }
                    for question in questions_by_repo[repo_id]
                ],
            }
            for repo_id in V2_DEVELOPMENT_REPOSITORIES
        ],
    }


def test_v2_manifest_loader_does_not_open_candidate_question_sets(tmp_path: Path) -> None:
    root = tmp_path
    entries = []
    for repo_id in V2_DEVELOPMENT_REPOSITORIES:
        question_path = root / repo_id / "questions.json"
        fixture_path = root / repo_id / "fixture.json.gz"
        question_path.parent.mkdir(parents=True)
        question_path.write_text("{}", encoding="utf-8")
        fixture_path.write_bytes(b"fixture")
        entry = _entries()[repo_id]
        entry["questions"]["sha256"] = sha256_file(question_path)
        entry["fixture"]["sha256"] = sha256_file(fixture_path)
        entries.append(entry)

    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": 2,
                "repositories": entries,
                "candidates": [{"questions": {"path": "missing-candidate-questions.json"}}],
            }
        ),
        encoding="utf-8",
    )

    loaded = load_v2_development_entries(manifest_path, root=root)

    assert tuple(loaded) == V2_DEVELOPMENT_REPOSITORIES
    assert not (root / "missing-candidate-questions.json").exists()


def test_v2_question_loader_selects_the_registered_development_ids(tmp_path: Path) -> None:
    questions = _questions("rq")
    question_ids = [question["id"] for question in questions]
    question_path = tmp_path / "rq" / "questions.json"
    question_path.parent.mkdir()
    question_path.write_text(
        json.dumps(
            {
                "repo_id": "rq",
                "pinned_sha": "rq-sha",
                "dataset_version": "2.0",
                "questions": questions,
            }
        ),
        encoding="utf-8",
    )
    entry = {
        "id": "rq",
        "pinned_sha": "rq-sha",
        "questions": {"path": "rq/questions.json"},
        "splits": {"development": question_ids, "held_out": [], "smoke": []},
    }

    selected = load_v2_development_questions(entry, root=tmp_path)

    assert [question["id"] for question in selected] == question_ids


def test_v2_guard_breakdown_keeps_near_miss_and_false_premise_distinct() -> None:
    rows = [
        {
            "category": "unanswerable_near",
            "kind": "near-miss",
            "guard_refused": False,
        },
        {
            "category": "unanswerable_near",
            "kind": "false-premise",
            "guard_refused": True,
        },
    ]

    breakdown = scorecard_module._kind_breakdown(rows)

    assert set(breakdown) == {"false-premise", "near-miss"}
    assert breakdown["false-premise"]["n"] == 1
    assert breakdown["near-miss"]["n"] == 1


def test_v2_rankings_export_uses_only_development_records(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _entries()
    questions_by_repo = {repo_id: _questions(repo_id) for repo_id in V2_DEVELOPMENT_REPOSITORIES}
    calls: list[tuple[str, int, int]] = []

    async def fake_run_offline_retrieval(**kwargs: Any) -> dict[str, Any]:
        repo_id = kwargs["repo_id"]
        records = kwargs["development_records"]
        calls.append((repo_id, kwargs["limit"], len(records)))
        return {
            "questions": [
                {"id": row["id"], "category": row["category"], "retrieved": []} for row in records
            ],
        }

    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(
        retrieval_eval,
        "load_v2_development_entries",
        lambda *_args, **_kwargs: entries,
    )
    monkeypatch.setattr(
        retrieval_eval,
        "load_v2_development_questions",
        lambda entry, **_kwargs: questions_by_repo[entry["id"]],
    )
    monkeypatch.setattr(retrieval_eval, "run_offline_retrieval", fake_run_offline_retrieval)
    monkeypatch.setattr(
        retrieval_eval.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="test-commit\n"),
    )

    output_path = tmp_path / "rankings.json"
    export = asyncio.run(
        retrieval_eval.export_v2_development_rankings(
            output_path,
            manifest_path=manifest_path,
            root=tmp_path,
        )
    )

    assert export["metadata"]["dataset_version"] == "v2"
    assert export["metadata"]["repository_ids"] == list(V2_DEVELOPMENT_REPOSITORIES)
    assert [row["id"] for row in export["repositories"]] == list(V2_DEVELOPMENT_REPOSITORIES)
    assert len(calls) == 8
    assert {(repo_id, limit) for repo_id, limit, _ in calls} == {
        (repo_id, limit) for repo_id in V2_DEVELOPMENT_REPOSITORIES for limit in (5, 20)
    }
    assert all(question_count == 40 for _, _, question_count in calls)
    assert b"\r\n" not in output_path.read_bytes()
    assert json.loads(output_path.read_text(encoding="utf-8")) == export


def test_v2_scorecard_writer_scores_development_only_without_v1_crosscheck(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    entries = _entries()
    questions_by_repo = {repo_id: _questions(repo_id) for repo_id in V2_DEVELOPMENT_REPOSITORIES}
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")
    input_path = tmp_path / "rankings.json"
    input_path.write_text(
        json.dumps(_export(manifest_path, questions_by_repo)),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        scorecard_module,
        "load_v2_development_entries",
        lambda *_args, **_kwargs: entries,
    )
    monkeypatch.setattr(
        scorecard_module,
        "load_v2_development_questions",
        lambda entry, **_kwargs: questions_by_repo[entry["id"]],
    )
    monkeypatch.setattr(scorecard_module, "load_fixture", lambda _path: {"chunks": []})
    monkeypatch.setattr(
        scorecard_module.subprocess,
        "run",
        lambda *_args, **_kwargs: SimpleNamespace(stdout="test-scorecard-commit\n"),
    )
    monkeypatch.setattr(scorecard_module, "span_hit_at_k", lambda *_args: False)
    monkeypatch.setattr(scorecard_module, "first_relevant_span_rank", lambda *_args: None)
    monkeypatch.setattr(scorecard_module, "ndcg_at_k", lambda *_args: 0.0)
    monkeypatch.setattr(scorecard_module, "context_precision_at_k", lambda *_args: 0.0)
    monkeypatch.setattr(scorecard_module, "recall_at_k", lambda *_args: 0.0)
    monkeypatch.setattr(
        scorecard_module,
        "_wilson",
        lambda successes, n, *, view: {
            "value": successes / n if n else None,
            "successes": successes,
            "n": n,
            "wilson_95": [0.0, 1.0],
            "view": view,
        },
    )
    monkeypatch.setattr(
        scorecard_module,
        "_bootstrap_mean",
        lambda rows_by_repo, _field, repo_ids, *, view: {
            "value": 0.0,
            "n": sum(len(rows_by_repo[repo_id]) for repo_id in repo_ids),
            "bootstrap_95": [0.0, 0.0],
            "view": view,
        },
    )
    monkeypatch.setattr(
        scorecard_module,
        "_auroc_metric",
        lambda rows_by_repo, repo_ids, *, view: {
            "value": None,
            "n": sum(len(rows_by_repo[repo_id]) for repo_id in repo_ids),
            "bootstrap_95": None,
            "view": view,
        },
    )
    monkeypatch.setattr(scorecard_module, "_threshold_sweep", lambda _rows: [])
    monkeypatch.setattr(
        scorecard_module,
        "verify_registered_crosscheck",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("v1 cross-check called")),
    )

    output_path = tmp_path / "scorecard.json"
    scorecard = scorecard_module.write_v2_scorecard(
        input_path,
        output_path,
        manifest_path=manifest_path,
        root=tmp_path,
    )

    assert output_path.is_file()
    assert scorecard["metadata"]["dataset_version"] == "v2"
    assert scorecard["metadata"]["repository_ids"] == list(V2_DEVELOPMENT_REPOSITORIES)
    assert scorecard["metadata"]["n"] == 160
    assert scorecard["pooled"]["answerable_n"] == 120
    assert scorecard["pooled"]["unanswerable_n"] == 40
    assert set(scorecard["per_repository"]) == set(V2_DEVELOPMENT_REPOSITORIES)
    assert b"\r\n" not in output_path.read_bytes()
    assert json.loads(output_path.read_text(encoding="utf-8")) == scorecard


def test_v2_scorecard_refuses_non_development_export(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        scorecard_module,
        "load_v2_development_entries",
        lambda *_args, **_kwargs: {},
    )

    with pytest.raises(ValueError, match="refuses any split other than development"):
        scorecard_module.build_v2_scorecard(
            {"metadata": {"split": "held_out"}},
            manifest_path=tmp_path / "manifest.json",
            root=tmp_path,
        )
