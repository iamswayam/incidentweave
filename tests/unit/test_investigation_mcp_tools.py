from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

import pytest

import app.investigation.graph as graph_module
from app.investigation.confidence import calibrate_confidence
from app.investigation.graph import create_investigation_graph
from app.investigation.mcp_server import grep_search


class FakeSessionContext:
    async def __aenter__(self) -> FakeSessionContext:
        return self

    async def __aexit__(self, *args: object) -> None:
        return None


def graph_state() -> dict[str, Any]:
    return {
        "repository_id": 4,
        "repository_name": "incidentweave-local",
        "repository_path": ".",
        "query": "quasarLatchOmega",
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
        "evidence_source": "hybrid",
        "tool_calls": [],
    }


def grep_match() -> dict[str, object]:
    return {
        "id": "grep-1",
        "repository_id": 4,
        "file_path": "src/fixture.py",
        "line_start": 1,
        "line_end": 1,
        "content": "# operational marker: quasarLatchOmega",
        "vector_score": None,
        "fts_score": None,
        "rrf_score": None,
    }


def response_payload() -> dict[str, object]:
    return {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                                "Diagnosis: The source contains quasarLatchOmega.\n"
                                "Confidence: high\n"
                                "Evidence used: src/fixture.py, lines 1-1"
                            )
                        }
                    ]
                }
            }
        ]
    }


def test_grep_search_finds_literal_case_insensitively_and_uses_ingest_exclusions(
    tmp_path: Path,
) -> None:
    source_dir = tmp_path / "src"
    source_dir.mkdir()
    (source_dir / "fixture.py").write_text(
        "# marker: QuasarLatchOmega\n", encoding="utf-8"
    )
    ignored_dir = tmp_path / ".venv"
    ignored_dir.mkdir()
    (ignored_dir / "ignored.py").write_text(
        "# marker: quasarLatchOmega\n", encoding="utf-8"
    )

    matches = grep_search(tmp_path, "quasarlatchomega", repository_id=4, limit=10)

    assert len(matches) == 1
    assert matches[0]["file_path"] == "src/fixture.py"
    assert matches[0]["line_start"] == matches[0]["line_end"] == 1
    assert matches[0]["content"] == "# marker: QuasarLatchOmega"
    assert matches[0]["vector_score"] is None
    assert matches[0]["fts_score"] is None
    assert matches[0]["rrf_score"] is None


@pytest.mark.anyio
async def test_graph_calls_grep_only_after_both_hybrid_attempts_and_traces_all_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[tuple[str, object]] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(("hybrid_search", limit))
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append(("grep_search", keyword))
        return [grep_match()], None

    def fake_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        return response_payload(), 25

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", fake_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == [
        ("hybrid_search", 5),
        ("hybrid_search", 10),
        ("grep_search", "quasarLatchOmega"),
    ]
    assert result["diagnosis"] == "The source contains quasarLatchOmega."
    assert result["retry_used"] is True
    assert result["evidence_source"] == "literal"
    assert [attempt["tool"] for attempt in result["tool_calls"]] == [
        "hybrid_search",
        "hybrid_search",
        "grep_search",
    ]
    assert [attempt["stage"] for attempt in result["tool_calls"]] == [
        "initial",
        "widened_retry",
        "literal_fallback",
    ]
    assert result["tool_calls"][2]["outcome"] == {
        "match_count": 1,
        "sufficient": True,
        "reason": "Literal source matches were found.",
    }


@pytest.mark.anyio
async def test_graph_returns_insufficient_when_grep_has_no_match(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events: list[str] = []

    async def fake_hybrid_search(
        session: object,
        repository_id: int,
        query_text: str,
        query_embedding: list[float],
        limit: int,
    ) -> list[dict[str, object]]:
        events.append(f"hybrid:{limit}")
        return [{"id": limit, "rrf_score": 0.02, "vector_score": 0.7}]

    async def fake_grep_search_mcp(
        repository_name: str,
        repository_path: str,
        keyword: str,
        limit: int,
    ) -> tuple[list[dict[str, object]], None]:
        events.append("grep")
        return [], None

    def unexpected_generation(prompt: str) -> tuple[Mapping[str, object], int]:
        raise AssertionError("Generation must not run without sufficient evidence")

    monkeypatch.setattr(graph_module, "AsyncSessionLocal", FakeSessionContext)
    monkeypatch.setattr(graph_module, "hybrid_search", fake_hybrid_search)
    monkeypatch.setattr(graph_module, "call_grep_search_mcp", fake_grep_search_mcp)
    monkeypatch.setattr(graph_module, "generate_investigation", unexpected_generation)

    result = await create_investigation_graph(calibrate_confidence).ainvoke(graph_state())

    assert events == ["hybrid:5", "hybrid:10", "grep"]
    assert result["diagnosis"] == "INSUFFICIENT_EVIDENCE"
    assert result["retry_count"] == 1
    assert len(result["tool_calls"]) == 3
    assert result["tool_calls"][-1]["outcome"]["sufficient"] is False
