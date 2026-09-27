from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def initial_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "query": "how are async sessions configured?",
        "query_embedding": [0.1, 0.2],
        "search_limit": 5,
        "retry_limit": 10,
        "retry_count": 0,
        "retry_used": False,
        "retrieval_results": [],
        "evidence_check": {},
        "diagnosis": "",
        "confidence": "",
        "cited_chunk_ids": [],
        "model": "",
        "latency_ms": None,
        "calibration_note": "",
        "confidence_calibrated": False,
    }


def sufficient_result() -> dict[str, object]:
    return {
        "id": 136,
        "file_path": "app/db/session.py",
        "line_start": 1,
        "line_end": 46,
        "vector_score": 0.3,
        "fts_score": 0.5,
        "rrf_score": 0.04,
        "content": "AsyncSessionLocal = async_sessionmaker(...) ",
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: AsyncSessionLocal uses async_sessionmaker.\n"
                                "Confidence: high\n"
                                "Evidence used: app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }


@pytest.mark.anyio
async def test_graph_retries_once_with_wider_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        if len(limits) == 1:
            return [{"id": 1, "rrf_score": 0.01, "vector_score": 0.3}]
        return [sufficient_result()]

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 12

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "AsyncSessionLocal uses async_sessionmaker."


@pytest.mark.anyio
async def test_graph_stops_after_one_insufficient_retry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    limits: list[int] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        limits.append(limit)
        return [{"id": len(limits), "rrf_score": 0.01, "vector_score": 0.3}]

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run after insufficient evidence")

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(initial_state())

    assert limits == [5, 10]
    assert result["retry_count"] == 1
    assert result["retry_used"] is True
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["confidence"] == "low"


def test_confidence_calibration_downgrades_borderline_retrieval() -> None:
    confidence, note = calibrate_confidence("high", 0.021, 0.3)

    assert confidence == "medium"
    assert "best RRF 0.021000 is below 0.032" in note
