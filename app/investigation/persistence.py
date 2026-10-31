"""Persist investigation results and retrieval audit rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict

from sqlalchemy import select

from app.db.models import Audit, IngestRun, Investigation
from app.investigation.parsing import parse_investigation_response
from app.investigation.replay import ReplayRecord

OUTCOME_ANSWERED = "answered"
OUTCOME_REFUSED_GUARD = "refused_guard"
OUTCOME_ABSTAINED_MODEL = "abstained_model"
OUTCOME_ERROR = "error"
OUTCOME_GENERATION_UNAVAILABLE = "generation_unavailable"


async def latest_ingest_run_id(session, repository_id: int) -> int | None:
    """Return the newest ingestion run for a repository, if one exists."""

    return await session.scalar(
        select(IngestRun.id)
        .where(IngestRun.repository_id == repository_id)
        .order_by(IngestRun.id.desc())
        .limit(1)
    )


def _retrieval_summary(
    retrieval_results: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "id": item.get("id"),
            "file_path": item.get("file_path"),
            "line_start": item.get("line_start"),
            "line_end": item.get("line_end"),
            "vector_score": item.get("vector_score"),
            "fts_score": item.get("fts_score"),
            "rrf_score": item.get("rrf_score"),
        }
        for item in retrieval_results
    ]


def content_free_tool_call_trace(
    tool_call_trace: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    """Keep degraded tool telemetry while omitting the natural-language query."""

    sanitized: list[dict[str, object]] = []
    for item in tool_call_trace:
        record = dict(item)
        parameters = record.get("parameters")
        if isinstance(parameters, Mapping):
            record["parameters"] = {
                key: value for key, value in parameters.items() if key != "query"
            }
        sanitized.append(record)
    return sanitized


def _replay_columns(replay: ReplayRecord | None) -> dict[str, object]:
    return asdict(replay) if replay is not None else {}


async def persist_investigation(
    session,
    repository_id: int,
    query: str,
    response_payload: Mapping[str, object],
    retrieval_results: Sequence[Mapping[str, object]],
    model: str,
    latency_ms: int,
    token_usage: int | None = None,
    final_confidence: str | None = None,
    tool_call_trace: Sequence[Mapping[str, object]] | None = None,
    ingest_run_id: int | None = None,
    replay: ReplayRecord | None = None,
) -> Investigation:
    """Create one Investigation row and one Audit row from a Gemini response."""

    parsed = parse_investigation_response(response_payload, retrieval_results)
    diagnosis = str(parsed.get("diagnosis") or "INSUFFICIENT_EVIDENCE")
    confidence = final_confidence or parsed.get("confidence")
    outcome = (
        OUTCOME_ABSTAINED_MODEL
        if diagnosis.rstrip(".").strip().upper() == "INSUFFICIENT_EVIDENCE"
        else OUTCOME_ANSWERED
    )
    retrieved_chunk_ids: list[int] = []
    for result in retrieval_results:
        chunk_id = result.get("id")
        if isinstance(chunk_id, int):
            retrieved_chunk_ids.append(chunk_id)
        elif isinstance(chunk_id, str) and chunk_id.isdigit():
            retrieved_chunk_ids.append(int(chunk_id))
    cited_chunk_ids = [str(chunk_id) for chunk_id in parsed.get("cited_chunk_ids", [])]

    investigation = Investigation(
        repository_id=repository_id,
        query=query,
        response=diagnosis,
        model=model,
        latency_ms=latency_ms,
        token_usage=token_usage,
        confidence=str(confidence) if confidence else None,
        outcome=outcome,
    )
    session.add(investigation)
    await session.flush()

    replay_columns = _replay_columns(replay)
    replay_columns["raw_self_rating"] = str(parsed["raw_self_rating"])
    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
        ingest_run_id=ingest_run_id,
        retrieved_chunk_ids=retrieved_chunk_ids,
        vector_scores=[
            float(item["vector_score"])
            for item in retrieval_results
            if isinstance(item.get("vector_score"), (int, float))
        ],
        fts_scores=[
            float(item["fts_score"])
            for item in retrieval_results
            if isinstance(item.get("fts_score"), (int, float))
        ],
        rrf_scores=[
            float(item["rrf_score"])
            for item in retrieval_results
            if isinstance(item.get("rrf_score"), (int, float))
        ],
        tool_calls={
            "attempts": [dict(item) for item in (tool_call_trace or [])],
            "cited_chunk_ids": cited_chunk_ids,
            "retrieval_results": _retrieval_summary(retrieval_results),
            "claims": parsed["claims"],
            "uncertainty_note": parsed["uncertainty_note"],
            "citation_validation": {
                "submitted": parsed["submitted_citation_count"],
                "valid": parsed["valid_citation_count"],
                "rate": parsed["citation_validity_rate"],
            },
        },
        model=model,
        response=diagnosis,
        latency_ms=latency_ms,
        token_usage=token_usage,
        confidence=str(confidence) if confidence else None,
        **replay_columns,
    )
    session.add(audit)
    await session.commit()
    return investigation


async def persist_refusal(
    session,
    repository_id: int,
    query: str,
    retrieval_results: Sequence[Mapping[str, object]],
    tool_call_trace: Sequence[Mapping[str, object]],
    ingest_run_id: int | None = None,
    replay: ReplayRecord | None = None,
) -> Investigation:
    """Persist a guard refusal and its retrieval evidence."""

    investigation = Investigation(
        repository_id=repository_id,
        query=query,
        response="INSUFFICIENT_EVIDENCE",
        model=None,
        latency_ms=None,
        token_usage=None,
        confidence="low",
        outcome=OUTCOME_REFUSED_GUARD,
    )
    session.add(investigation)
    await session.flush()

    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
        ingest_run_id=ingest_run_id,
        retrieved_chunk_ids=[
            int(chunk_id)
            for item in retrieval_results
            if (chunk_id := item.get("id")) is not None
            and (isinstance(chunk_id, int) or (isinstance(chunk_id, str) and chunk_id.isdigit()))
        ],
        vector_scores=[
            float(item["vector_score"])
            for item in retrieval_results
            if isinstance(item.get("vector_score"), (int, float))
        ],
        fts_scores=[
            float(item["fts_score"])
            for item in retrieval_results
            if isinstance(item.get("fts_score"), (int, float))
        ],
        rrf_scores=[
            float(item["rrf_score"])
            for item in retrieval_results
            if isinstance(item.get("rrf_score"), (int, float))
        ],
        tool_calls={
            "attempts": [dict(item) for item in tool_call_trace],
            "cited_chunk_ids": [],
            "retrieval_results": _retrieval_summary(retrieval_results),
            "claims": [],
            "uncertainty_note": (
                str(tool_call_trace[-1].get("outcome", {}).get("reason") or "")
                if tool_call_trace
                and isinstance(tool_call_trace[-1].get("outcome"), Mapping)
                else ""
            ),
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
        },
        model=None,
        response="INSUFFICIENT_EVIDENCE",
        latency_ms=None,
        token_usage=None,
        confidence="low",
        **_replay_columns(replay),
    )
    session.add(audit)
    await session.commit()
    return investigation


async def persist_generation_unavailable(
    session,
    repository_id: int,
    query: str,
    retrieval_results: Sequence[Mapping[str, object]],
    evidence: Sequence[Mapping[str, object]],
    evidence_check: Mapping[str, object],
    tool_call_trace: Sequence[Mapping[str, object]],
    generation_trace: Mapping[str, object],
    ingest_run_id: int | None = None,
    replay: ReplayRecord | None = None,
) -> Investigation:
    """Persist an unavailable generation outcome without prompt or source text."""

    investigation = Investigation(
        repository_id=repository_id,
        query=query,
        response="",
        model=None,
        latency_ms=None,
        token_usage=None,
        confidence="not_applicable",
        outcome=OUTCOME_GENERATION_UNAVAILABLE,
    )
    session.add(investigation)
    await session.flush()

    retrieved_chunk_ids = [
        int(chunk_id)
        for item in retrieval_results
        if (chunk_id := item.get("id")) is not None
        and (isinstance(chunk_id, int) or (isinstance(chunk_id, str) and chunk_id.isdigit()))
    ]
    evidence_items = [dict(item) for item in evidence]
    replay_columns = _replay_columns(replay)
    replay_columns["trace"] = dict(generation_trace)
    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
        ingest_run_id=ingest_run_id,
        retrieved_chunk_ids=retrieved_chunk_ids,
        vector_scores=[
            float(item["vector_score"])
            for item in retrieval_results
            if isinstance(item.get("vector_score"), (int, float))
        ],
        fts_scores=[
            float(item["fts_score"])
            for item in retrieval_results
            if isinstance(item.get("fts_score"), (int, float))
        ],
        rrf_scores=[
            float(item["rrf_score"])
            for item in retrieval_results
            if isinstance(item.get("rrf_score"), (int, float))
        ],
        tool_calls={
            "attempts": content_free_tool_call_trace(tool_call_trace),
            "cited_chunk_ids": [],
            "retrieval_results": _retrieval_summary(retrieval_results),
            "claims": [],
            "uncertainty_note": (
                "Generation unavailable after configured provider retries."
            ),
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
            "degraded": {
                "unavailable_answer": True,
                "degraded": True,
                "degraded_reason": "generation_unavailable",
                "evidence": evidence_items,
                "evidence_check": dict(evidence_check),
            },
        },
        model=None,
        response="",
        latency_ms=None,
        token_usage=None,
        confidence="not_applicable",
        **replay_columns,
    )
    session.add(audit)
    await session.commit()
    return investigation


async def persist_error(
    session,
    repository_id: int,
    query: str,
    error_class: str,
    ingest_run_id: int | None = None,
    replay: ReplayRecord | None = None,
) -> Investigation:
    """Persist an investigation failure without storing its exception message."""

    investigation = Investigation(
        repository_id=repository_id,
        query=query,
        response=None,
        model=None,
        latency_ms=None,
        token_usage=None,
        confidence=None,
        outcome=OUTCOME_ERROR,
        error_class=error_class,
    )
    session.add(investigation)
    await session.flush()

    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
        ingest_run_id=ingest_run_id,
        retrieved_chunk_ids=[],
        vector_scores=[],
        fts_scores=[],
        rrf_scores=[],
        tool_calls={
            "attempts": [],
            "cited_chunk_ids": [],
            "retrieval_results": [],
            "claims": [],
            "uncertainty_note": "",
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
        },
        model=None,
        response=None,
        latency_ms=None,
        token_usage=None,
        confidence=None,
        **_replay_columns(replay),
    )
    session.add(audit)
    await session.commit()
    return investigation
