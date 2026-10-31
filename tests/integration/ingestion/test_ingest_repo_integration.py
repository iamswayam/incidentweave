"""Database integration tests for content-addressed repository ingestion."""

from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy import delete, select

import scripts.investigate as investigate_module
from app.db.models import Audit, Chunk, IngestRun, Repository
from app.db.session import AsyncSessionLocal
from scripts.ingest_repo import CHUNKER_VERSION, ingest_repository

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_ingest_upserts_chunks_and_links_audit_to_latest_run(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository_name = f"ingest-upsert-{uuid4().hex}"
    alpha_path = tmp_path / "alpha.py"
    beta_path = tmp_path / "beta.py"
    gamma_path = tmp_path / "gamma.py"
    alpha_path.write_text("ALPHA = 'old'\n", encoding="utf-8")
    beta_path.write_text("BETA_CONTENT = 'removed'\n", encoding="utf-8")
    gamma_path.write_text("GAMMA = 'stable'\n", encoding="utf-8")
    repo_id: int | None = None

    try:
        assert await ingest_repository(str(tmp_path), repository_name) == (3, 3)
        async with AsyncSessionLocal() as session:
            repository = await session.scalar(
                select(Repository).where(Repository.name == repository_name)
            )
            assert repository is not None
            repo_id = repository.id
            initial_chunks = list(
                (
                    await session.scalars(
                        select(Chunk)
                        .where(Chunk.repository_id == repo_id)
                        .order_by(Chunk.file_path)
                    )
                ).all()
            )
            initial_ids = {chunk.file_path: chunk.id for chunk in initial_chunks}
            alpha_chunk = next(chunk for chunk in initial_chunks if chunk.file_path == "alpha.py")
            alpha_chunk.embedding = [0.0] * 768
            await session.commit()

        assert await ingest_repository(str(tmp_path), repository_name) == (3, 3)
        async with AsyncSessionLocal() as session:
            unchanged_chunks = list(
                (
                    await session.scalars(
                        select(Chunk)
                        .where(Chunk.repository_id == repo_id)
                        .order_by(Chunk.file_path)
                    )
                ).all()
            )
            assert {chunk.file_path: chunk.id for chunk in unchanged_chunks} == initial_ids
            unchanged_alpha = next(
                chunk for chunk in unchanged_chunks if chunk.file_path == "alpha.py"
            )
            assert unchanged_alpha.embedding == [0.0] * 768
            runs = list(
                (
                    await session.scalars(
                        select(IngestRun)
                        .where(IngestRun.repository_id == repo_id)
                        .order_by(IngestRun.id)
                    )
                ).all()
            )
            assert len(runs) == 2
            assert runs[-1].source_path == str(tmp_path.resolve())
            assert runs[-1].commit_sha is None
            assert runs[-1].chunker_version == CHUNKER_VERSION

        alpha_path.write_text("ALPHA = 'edited'\n", encoding="utf-8")
        beta_path.unlink()
        assert await ingest_repository(str(tmp_path), repository_name) == (2, 2)

        async with AsyncSessionLocal() as session:
            final_chunks = list(
                (
                    await session.scalars(
                        select(Chunk)
                        .where(Chunk.repository_id == repo_id)
                        .order_by(Chunk.file_path)
                    )
                ).all()
            )
            final_ids = {chunk.file_path: chunk.id for chunk in final_chunks}
            assert final_ids["alpha.py"] != initial_ids["alpha.py"]
            assert final_ids["gamma.py"] == initial_ids["gamma.py"]
            assert "beta.py" not in final_ids
            assert all("BETA_CONTENT" not in chunk.content for chunk in final_chunks)

        async def fake_ainvoke(state: dict[str, object]) -> dict[str, object]:
            del state
            return {
                "evidence_check": {"is_sufficient": True},
                "diagnosis": "The alpha value changed.",
                "confidence": "high",
                "cited_chunk_ids": ["136"],
                "retrieval_results": [
                    {
                        "id": 136,
                        "file_path": "alpha.py",
                        "line_start": 1,
                        "line_end": 1,
                        "vector_score": 0.2,
                        "fts_score": None,
                        "rrf_score": 0.05,
                        "content": "ALPHA = 'edited'",
                    }
                ],
                "model": "test-model",
                "latency_ms": 1,
                "retry_used": False,
                "confidence_calibrated": False,
                "calibration_note": "",
                "tool_calls": [],
                "response_payload": {
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": json.dumps(
                                            {
                                                "outcome": "answered",
                                                "diagnosis": "The alpha value changed.",
                                                "self_rating": "high",
                                                "uncertainty_note": "",
                                                "claims": [
                                                    {
                                                        "text": "The alpha value changed.",
                                                        "evidence": [
                                                            {
                                                                "chunk_id": "136",
                                                                "quote": "ALPHA = 'edited'",
                                                            }
                                                        ],
                                                    }
                                                ],
                                            }
                                        )
                                    }
                                ]
                            }
                        }
                    ]
                },
            }

        class FakeGraph:
            async def ainvoke(self, state: dict[str, object]) -> dict[str, object]:
                return await fake_ainvoke(state)

        async def fake_embed_text(query: str) -> list[float]:
            return [0.0]

        monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
        monkeypatch.setattr(
            investigate_module,
            "create_investigation_graph",
            lambda calibrator: FakeGraph(),
        )
        result = await investigate_module.investigate_repository(
            repository_name,
            "What changed?",
            persist=True,
        )
        assert result["outcome"] == "answered"

        async with AsyncSessionLocal() as session:
            latest_run = await session.scalar(
                select(IngestRun)
                .where(IngestRun.repository_id == repo_id)
                .order_by(IngestRun.id.desc())
                .limit(1)
            )
            assert latest_run is not None
            audit = await session.scalar(
                select(Audit).where(Audit.repository_id == repo_id)
            )
            assert audit is not None
            assert audit.ingest_run_id == latest_run.id
    finally:
        async with AsyncSessionLocal() as session:
            await session.execute(
                delete(Repository).where(Repository.name == repository_name)
            )
            await session.commit()
