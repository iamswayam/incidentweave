from __future__ import annotations

import pytest

from app.db.models import Audit
from app.investigation.persistence import persist_investigation


class FakeSession:
    def __init__(self) -> None:
        self.added: list[object] = []
        self.committed = False

    def add(self, obj: object) -> None:
        self.added.append(obj)

    def add_all(self, objs: list[object]) -> None:
        self.added.extend(objs)

    async def flush(self) -> None:
        return None

    async def commit(self) -> None:
        self.committed = True


@pytest.mark.anyio
async def test_persist_investigation_creates_investigation_and_audit_rows() -> None:
    session = FakeSession()
    retrieval_results = [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
            "vector_score": 0.288488584,
            "fts_score": 0.5,
            "rrf_score": 0.032786885,
            "content": (
                "AsyncSessionLocal = async_sessionmaker(bind=engine, "
                "class_=AsyncSession, expire_on_commit=False)"
            ),
        },
        {
            "id": 106,
            "file_path": "tests/conftest.py",
            "line_start": 1,
            "line_end": 11,
            "vector_score": 0.4,
            "fts_score": None,
            "rrf_score": 0.016,
            "content": "asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())",
        },
    ]
    response_payload = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "text": (
                            "Diagnosis: Async sessions are configured using async_sessionmaker.\n\n"
                            "Confidence: high\n\n"
                            "Evidence used:\n- app/db/session.py, lines 1-46"
                            )
                        }
                    ]
                }
            }
        ]
    }
    tool_call_trace = [
        {
            "tool": "hybrid_search",
            "stage": "initial",
            "parameters": {"limit": 5},
            "outcome": {"result_count": 5, "sufficient": False},
        },
        {
            "tool": "hybrid_search",
            "stage": "widened_retry",
            "parameters": {"limit": 10},
            "outcome": {"result_count": 10, "sufficient": False},
        },
        {
            "tool": "grep_search",
            "stage": "literal_fallback",
            "parameters": {"keyword": "async_sessionmaker"},
            "outcome": {"match_count": 1, "sufficient": True},
        },
    ]

    investigation = await persist_investigation(
        session=session,
        repository_id=17,
        query="how are async sessions configured?",
        response_payload=response_payload,
        retrieval_results=retrieval_results,
        model="gemini-3.5-flash-lite",
        latency_ms=2400,
        token_usage=128,
        final_confidence="medium",
        tool_call_trace=tool_call_trace,
    )

    assert investigation.query == "how are async sessions configured?"
    assert investigation.response == "Async sessions are configured using async_sessionmaker."
    assert investigation.model == "gemini-3.5-flash-lite"
    assert investigation.latency_ms == 2400
    assert investigation.token_usage == 128
    assert investigation.confidence == "medium"
    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert len(audit_rows) == 1
    assert audit_rows[0].retrieved_chunk_ids == [105, 106]
    assert audit_rows[0].vector_scores == [0.288488584, 0.4]
    assert audit_rows[0].fts_scores == [0.5]
    assert audit_rows[0].rrf_scores == [0.032786885, 0.016]
    assert audit_rows[0].tool_calls["cited_chunk_ids"] == ["105"]
    assert audit_rows[0].tool_calls["attempts"] == tool_call_trace
    assert audit_rows[0].confidence == "medium"
