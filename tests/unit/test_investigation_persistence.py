from __future__ import annotations

import pytest

from app.db.models import Audit
from app.investigation.parsing import parse_investigation_response
from app.investigation.persistence import (
    OUTCOME_ABSTAINED_MODEL,
    OUTCOME_ANSWERED,
    OUTCOME_ERROR,
    OUTCOME_REFUSED_GUARD,
    persist_error,
    persist_investigation,
    persist_refusal,
)
from app.investigation.replay import ReplayRecord


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
                                "Diagnosis: Async sessions are configured using "
                                "async_sessionmaker.\n\n"
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
        ingest_run_id=231,
        replay=ReplayRecord(
            prompt="grounded prompt",
            prompt_version="grounded-v2",
            raw_response=(
                "Diagnosis: Async sessions are configured using async_sessionmaker.\n"
                "Confidence: high\nEvidence used: app/db/session.py"
            ),
            raw_self_rating="high",
            generation_params={"timeout_seconds": 60, "max_attempts": 3},
            thresholds={"max_evidence_chars": 24000},
            embedding_model="models/gemini-embedding-001",
            chunk_records=[
                {
                    "chunk_id": "105",
                    "rank": 1,
                    "content_hash": "hash-105",
                    "kept_in_prompt": True,
                }
            ],
            trace={
                "correlation_id": "abc123",
                "outcome": "answered",
                "model": "gemini-3.5-flash-lite",
                "generation_latency_ms": 2400,
                "error_class": None,
            },
        ),
    )

    assert investigation.query == "how are async sessions configured?"
    assert investigation.response == "Async sessions are configured using async_sessionmaker."
    assert investigation.model == "gemini-3.5-flash-lite"
    assert investigation.latency_ms == 2400
    assert investigation.token_usage == 128
    assert investigation.confidence == "medium"
    assert investigation.outcome == OUTCOME_ANSWERED
    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert len(audit_rows) == 1
    assert audit_rows[0].retrieved_chunk_ids == [105, 106]
    assert audit_rows[0].vector_scores == [0.288488584, 0.4]
    assert audit_rows[0].fts_scores == [0.5]
    assert audit_rows[0].rrf_scores == [0.032786885, 0.016]
    assert audit_rows[0].tool_calls["cited_chunk_ids"] == ["105"]
    assert audit_rows[0].tool_calls["attempts"] == tool_call_trace
    assert audit_rows[0].confidence == "medium"
    assert audit_rows[0].ingest_run_id == 231
    audit = audit_rows[0]
    assert audit.prompt == "grounded prompt"
    assert audit.prompt_version == "grounded-v2"
    assert audit.raw_self_rating == "high"
    assert audit.chunk_records[0]["kept_in_prompt"] is True
    reparsed = parse_investigation_response(
        {
            "candidates": [
                {"content": {"parts": [{"text": audit.raw_response}]}}
            ]
        },
        retrieval_results,
    )
    assert reparsed["diagnosis"] == investigation.response
    assert reparsed["confidence"] == "high"


@pytest.mark.anyio
async def test_persist_investigation_marks_model_abstention() -> None:
    session = FakeSession()
    investigation = await persist_investigation(
        session=session,
        repository_id=17,
        query="question",
        response_payload={
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {"text": "Diagnosis: insufficient_evidence.\nConfidence: medium"}
                        ]
                    }
                }
            ]
        },
        retrieval_results=[],
        model="gemini-3.5-flash-lite",
        latency_ms=1200,
        ingest_run_id=234,
    )

    assert investigation.outcome == OUTCOME_ABSTAINED_MODEL
    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert len(audit_rows) == 1
    assert audit_rows[0].ingest_run_id == 234


@pytest.mark.anyio
async def test_persist_refusal_creates_investigation_and_audit() -> None:
    session = FakeSession()
    retrieval_results = [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
            "vector_score": 0.7,
            "fts_score": None,
            "rrf_score": 0.02,
            "content": "source evidence",
        }
    ]
    trace = [
        {
            "tool": "hybrid_search",
            "stage": "widened_retry",
            "outcome": {
                "sufficient": False,
                "reason": "Best vector distance is above the maximum threshold.",
                "best_rrf_score": 0.02,
                "best_vector_score": 0.7,
            },
        }
    ]

    investigation = await persist_refusal(
        session,
        repository_id=17,
        query="question",
        retrieval_results=retrieval_results,
        tool_call_trace=trace,
        ingest_run_id=232,
        replay=ReplayRecord(
            thresholds={"max_acceptable_vector_distance": 0.5},
            embedding_model="models/gemini-embedding-001",
            chunk_records=[
                {
                    "chunk_id": "105",
                    "rank": 1,
                    "content_hash": "hash-105",
                    "kept_in_prompt": False,
                }
            ],
            trace={
                "correlation_id": "refusal123",
                "outcome": OUTCOME_REFUSED_GUARD,
                "model": None,
                "generation_latency_ms": None,
                "error_class": None,
            },
        ),
    )

    audit_rows = [item for item in session.added if isinstance(item, Audit)]
    assert investigation.outcome == OUTCOME_REFUSED_GUARD
    assert investigation.response == "INSUFFICIENT_EVIDENCE"
    assert investigation.confidence == "low"
    assert investigation.model is None
    assert investigation.latency_ms is None
    assert len(audit_rows) == 1
    assert audit_rows[0].retrieved_chunk_ids == [105]
    assert audit_rows[0].vector_scores == [0.7]
    assert audit_rows[0].tool_calls["attempts"] == trace
    assert audit_rows[0].tool_calls["cited_chunk_ids"] == []
    assert audit_rows[0].tool_calls["retrieval_results"] == [
        {
            "id": 105,
            "file_path": "app/db/session.py",
            "line_start": 1,
            "line_end": 46,
            "vector_score": 0.7,
            "fts_score": None,
            "rrf_score": 0.02,
        }
    ]
    assert audit_rows[0].ingest_run_id == 232
    assert audit_rows[0].prompt is None
    assert audit_rows[0].raw_response is None
    assert audit_rows[0].chunk_records[0]["kept_in_prompt"] is False
    assert audit_rows[0].trace["outcome"] == OUTCOME_REFUSED_GUARD


@pytest.mark.anyio
async def test_persist_error_stores_only_exception_class_name() -> None:
    class SecretError(RuntimeError):
        pass

    session = FakeSession()
    error = SecretError("SECRET must not be persisted")
    investigation = await persist_error(
        session,
        repository_id=17,
        query="question",
        error_class=type(error).__name__,
        ingest_run_id=233,
        replay=ReplayRecord(
            trace={
                "correlation_id": "error123",
                "outcome": OUTCOME_ERROR,
                "model": "gemini-3.5-flash-lite",
                "generation_latency_ms": None,
                "error_class": "SecretError",
            }
        ),
    )
    audit_rows = [item for item in session.added if isinstance(item, Audit)]

    assert investigation.outcome == OUTCOME_ERROR
    assert investigation.error_class == "SecretError"
    assert investigation.response is None
    assert len(audit_rows) == 1
    assert audit_rows[0].tool_calls == {
        "attempts": [],
        "cited_chunk_ids": [],
        "retrieval_results": [],
    }
    assert audit_rows[0].ingest_run_id == 233
    assert audit_rows[0].trace["error_class"] == "SecretError"
    assert audit_rows[0].prompt is None
    assert audit_rows[0].raw_response is None
    assert "SECRET" not in repr(
        (
            investigation.error_class,
            investigation.response,
            audit_rows[0].response,
            audit_rows[0].tool_calls,
        )
    )
