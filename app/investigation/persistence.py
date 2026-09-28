"""Persist investigation results and retrieval audit rows."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from app.db.models import Audit, Investigation
from app.investigation.parsing import parse_investigation_response


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
) -> Investigation:
    """Create one Investigation row and one Audit row from a Gemini response."""

    parsed = parse_investigation_response(response_payload, retrieval_results)
    diagnosis = str(parsed.get("diagnosis") or "INSUFFICIENT_EVIDENCE")
    confidence = final_confidence or parsed.get("confidence")
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
    )
    session.add(investigation)
    await session.flush()

    audit = Audit(
        investigation_id=investigation.id,
        query=query,
        repository_id=repository_id,
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
            "retrieval_results": [
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
            ],
        },
        model=model,
        response=diagnosis,
        latency_ms=latency_ms,
        token_usage=token_usage,
        confidence=str(confidence) if confidence else None,
    )
    session.add(audit)
    await session.commit()
    return investigation
