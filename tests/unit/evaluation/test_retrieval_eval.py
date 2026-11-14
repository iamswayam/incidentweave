from __future__ import annotations

import asyncio
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

import evaluation.retrieval_eval as retrieval_eval


def test_v1_rankings_export_ignores_v2_repositories(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_ids = [
        "batch-processing-service",
        "incidentweave",
        "lifeos",
    ]
    manifest = {
        "schema_version": 2,
        "repositories": [{"id": repo_id} for repo_id in repository_ids]
        + [{"id": "luigi", "role": "development"}],
    }
    calls: list[str] = []

    async def fake_run_offline_retrieval(**kwargs: Any) -> dict[str, Any]:
        calls.append(kwargs["repo_id"])
        return {
            "questions": [
                {"id": "question-1", "category": "direct", "retrieved": []},
            ],
        }

    monkeypatch.setattr(retrieval_eval, "load_manifest", lambda *args, **kwargs: manifest)
    monkeypatch.setattr(
        retrieval_eval,
        "run_offline_retrieval",
        fake_run_offline_retrieval,
    )
    monkeypatch.setattr(
        retrieval_eval.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(stdout="test-commit\n"),
    )
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text("{}", encoding="utf-8")

    export = asyncio.run(
        retrieval_eval.export_development_rankings(
            tmp_path / "rankings.json",
            manifest_path=manifest_path,
            root=tmp_path,
        )
    )

    assert [repository["id"] for repository in export["repositories"]] == repository_ids
    assert set(calls) == set(repository_ids)
