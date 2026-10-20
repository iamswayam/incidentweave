from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

import scripts.investigate as investigate_module


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
    monkeypatch.setattr(investigate_module, "embed_text", lambda query: [0.1, 0.2])
    monkeypatch.setattr(
        investigate_module, "create_investigation_graph", lambda calibrator: fake_graph
    )

    result = await investigate_module.investigate_repository(
        "test-repo", "test query", limit=limit, persist=False
    )

    assert result["diagnosis"] == "test diagnosis"
    assert fake_graph.state is not None
    assert fake_graph.state["search_limit"] == limit
