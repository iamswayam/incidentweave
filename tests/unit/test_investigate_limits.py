from __future__ import annotations

import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

import scripts.investigate as investigate_module
from app.investigation.replay import ReplayRecord


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None

    async def scalar(self, statement: object) -> SimpleNamespace:
        return SimpleNamespace(id=1)


class FakeGraph:
    def __init__(self) -> None:
        self.state: dict[str, Any] | None = None

    async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
        self.state = state
        return {
            "evidence_check": {"is_sufficient": True},
            "response_payload": {"candidates": []},
            "diagnosis": "test diagnosis",
            "confidence": "low",
            "cited_chunk_ids": [],
            "retrieval_results": [],
            "model": "test-model",
            "latency_ms": 1,
            "retry_used": False,
            "confidence_calibrated": False,
            "calibration_note": "",
            "tool_calls": [],
            "prompt": "test prompt",
        }


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("limit", "query", "message"),
    [
        (0, "test", "--limit must be between 1 and 20"),
        (21, "test", "--limit must be between 1 and 20"),
        (1, "q" * 2001, "--query must be at most 2000 characters"),
    ],
)
async def test_investigate_repository_rejects_input_caps_before_database(
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
    query: str,
    message: str,
) -> None:
    def unexpected_database_access() -> None:
        raise AssertionError("Database access should not occur for invalid inputs")

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", unexpected_database_access)

    with pytest.raises(ValueError) as error:
        await investigate_module.investigate_repository("test-repo", query, limit=limit)
    assert str(error.value) == message


@pytest.mark.anyio
@pytest.mark.parametrize("limit", [1, 20])
async def test_investigate_repository_accepts_limit_bounds_without_external_services(
    monkeypatch: pytest.MonkeyPatch,
    limit: int,
) -> None:
    fake_graph = FakeGraph()
    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: fake_graph
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "test query", limit=limit, persist=False, temperature=0
    )

    assert result["diagnosis"] == "test diagnosis"
    assert fake_graph.state is not None
    assert fake_graph.state["search_limit"] == limit
    assert fake_graph.state["temperature"] == 0


@pytest.mark.anyio
@pytest.mark.parametrize("persist", [True, False])
async def test_investigate_repository_persists_guard_refusal_when_requested(
    monkeypatch: pytest.MonkeyPatch,
    persist: bool,
) -> None:
    class InsufficientGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            return {
                "evidence_check": {
                    "is_sufficient": False,
                    "reason": "No vector similarity score was retrieved.",
                },
                "diagnosis": "INSUFFICIENT_EVIDENCE",
                "confidence": "low",
                "cited_chunk_ids": [],
                "retrieval_results": [{"id": 9, "file_path": "source.py"}],
                "model": "test-model",
                "latency_ms": None,
                "retry_used": True,
                "confidence_calibrated": False,
                "calibration_note": "",
                "tool_calls": [{"stage": "widened_retry"}],
            }

    persisted_calls: list[tuple[object, ...]] = []

    async def fake_persist_refusal(
        session: object,
        repository_id: int,
        query: str,
        retrieval_results: list[dict[str, object]],
        tool_call_trace: list[dict[str, object]],
        ingest_run_id: int | None = None,
        replay: ReplayRecord | None = None,
    ) -> SimpleNamespace:
        persisted_calls.append(
            (repository_id, query, retrieval_results, tool_call_trace, ingest_run_id, replay)
        )
        return SimpleNamespace(id=71)

    async def fake_latest_ingest_run_id(session: object, repository_id: int) -> int:
        del session, repository_id
        return 42

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: InsufficientGraph()
    )
    monkeypatch.setattr(investigate_module, "persist_refusal", fake_persist_refusal)
    monkeypatch.setattr(
        investigate_module, "latest_ingest_run_id", fake_latest_ingest_run_id
    )

    result = await investigate_module.investigate_repository(
        "test-repo",
        "question",
        persist=persist,
    )

    assert result["outcome"] == "refused_guard"
    assert result["investigation_id"] == (71 if persist else None)
    assert len(persisted_calls) == (1 if persist else 0)
    if persist:
        assert persisted_calls[0][-2] == 42
        replay = persisted_calls[0][-1]
        assert isinstance(replay, ReplayRecord)
        assert replay.prompt is None
        assert replay.raw_response is None
        assert replay.chunk_records is not None
        assert replay.chunk_records[0]["kept_in_prompt"] is False
        assert replay.trace is not None
        assert replay.trace["outcome"] == "refused_guard"


@pytest.mark.anyio
async def test_investigation_deadline_persists_timeout_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    persisted_errors: list[str] = []

    class SlowGraph:
        async def ainvoke(self, state: dict[str, Any]) -> dict[str, Any]:
            await asyncio.Event().wait()
            return state

    async def fake_embed_text(query: str) -> list[float]:
        return [0.1, 0.2]

    async def fake_persist_error(
        session: object,
        repository_id: int,
        query: str,
        error_class: str,
        **kwargs: object,
    ) -> None:
        persisted_errors.append(error_class)

    monkeypatch.setattr(investigate_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(investigate_module, "embed_text", fake_embed_text)
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: SlowGraph()
    )
    monkeypatch.setattr(
        investigate_module, "persist_error", fake_persist_error
    )
    monkeypatch.setattr(investigate_module, "INVESTIGATION_DEADLINE_SECONDS", 0.01)

    with pytest.raises(TimeoutError):
        await investigate_module.investigate_repository(
            "test-repo", "question", persist=True
        )

    assert persisted_errors == ["TimeoutError"]
