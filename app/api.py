"""HTTP routes for persisted investigations and repository summaries."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api_security import require_api_access
from app.db.models import Audit, Chunk, Investigation, Repository
from app.db.session import AsyncSessionLocal
from scripts.investigate import investigate_repository

router = APIRouter()

EVALUATION_NOTE = (
    "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only "
    "(hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, "
    "and no tested vector-distance cutoff separated the groups. These results are "
    "diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
)


class InvestigationRequest(BaseModel):
    """Input for one synchronous grounded investigation."""

    repository_name: str = Field(min_length=1, max_length=255)
    query: str = Field(min_length=1)
    limit: int = Field(default=5, gt=0)


class InvestigationResponse(BaseModel):
    """Investigation output with calibrated and raw confidence context."""

    investigation_id: int | None
    repository_name: str
    query: str
    diagnosis: str
    confidence: str
    raw_confidence: str | None
    cited_chunk_ids: list[str]
    evidence_check: dict[str, Any]
    retry_used: bool
    tool_calls: list[dict[str, Any]]
    model: str
    latency_ms: int | None
    evaluation_note: str


class RepositorySummary(BaseModel):
    """Read-only repository chunk and embedding counts."""

    name: str
    chunk_count: int
    embedded_chunk_count: int


def _http_error(status_code: int, code: str, message: str) -> HTTPException:
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message},
    )


@router.post(
    "/investigations",
    response_model=InvestigationResponse,
    dependencies=[Depends(require_api_access)],
)
async def create_investigation(payload: InvestigationRequest) -> InvestigationResponse:
    """Run and persist one investigation synchronously."""

    try:
        result = await investigate_repository(
            payload.repository_name,
            payload.query,
            limit=payload.limit,
            persist=True,
        )
    except ValueError as exc:
        if str(exc).startswith("Repository not found:"):
            raise _http_error(404, "repository_not_found", "Repository not found.") from exc
        raise _http_error(
            422,
            "validation_error",
            "Request validation failed.",
        ) from exc
    except RuntimeError as exc:
        raise _http_error(
            502,
            "upstream_failure",
            "The investigation provider failed after its retries.",
        ) from exc

    confidence = str(result.get("confidence") or "low")
    calibrated = bool(result.get("confidence_calibrated"))
    raw_confidence = "high" if calibrated else confidence
    evidence_check = result.get("evidence_check")
    if not isinstance(evidence_check, dict):
        evidence_check = {}
    tool_calls = result.get("tool_calls")
    if not isinstance(tool_calls, list):
        tool_calls = []
    cited_chunk_ids = result.get("cited_chunk_ids")
    if not isinstance(cited_chunk_ids, list):
        cited_chunk_ids = []

    return InvestigationResponse(
        investigation_id=(
            int(result["investigation_id"])
            if isinstance(result.get("investigation_id"), int)
            else None
        ),
        repository_name=str(result.get("repository") or payload.repository_name),
        query=str(result.get("query") or payload.query),
        diagnosis=str(result.get("diagnosis") or "INSUFFICIENT_EVIDENCE"),
        confidence=confidence,
        raw_confidence=raw_confidence,
        cited_chunk_ids=[str(chunk_id) for chunk_id in cited_chunk_ids],
        evidence_check=evidence_check,
        retry_used=bool(result.get("retry_used")),
        tool_calls=tool_calls,
        model=str(result.get("model") or ""),
        latency_ms=(
            int(result["latency_ms"])
            if isinstance(result.get("latency_ms"), int)
            else None
        ),
        evaluation_note=EVALUATION_NOTE,
    )


@router.get(
    "/investigations/{investigation_id}",
    response_model=InvestigationResponse,
    dependencies=[Depends(require_api_access)],
)
async def get_investigation(investigation_id: int) -> InvestigationResponse:
    """Fetch a persisted investigation and its audit trace."""

    async with AsyncSessionLocal() as session:
        investigation = await session.get(Investigation, investigation_id)
        if investigation is None:
            raise _http_error(404, "investigation_not_found", "Investigation not found.")
        repository = await session.get(Repository, investigation.repository_id)
        audits = (
            await session.execute(
                select(Audit).where(Audit.investigation_id == investigation.id)
            )
        ).scalars().all()

    if len(audits) != 1:
        raise _http_error(
            500,
            "audit_invariant_violation",
            "The stored investigation audit record is unavailable.",
        )
    audit = audits[0]
    audit_payload = audit.tool_calls if isinstance(audit.tool_calls, dict) else {}
    attempts = audit_payload.get("attempts")
    tool_calls = (
        [item for item in attempts if isinstance(item, dict)]
        if isinstance(attempts, list)
        else []
    )
    latest_attempt = tool_calls[-1] if tool_calls else None
    latest_check = (
        latest_attempt.get("outcome")
        if latest_attempt and isinstance(latest_attempt.get("outcome"), dict)
        else {}
    )
    evidence_check = {
        "is_sufficient": latest_check.get("sufficient"),
        "reason": latest_check.get("reason", "Stored evidence check is unavailable."),
        "best_rrf_score": latest_check.get("best_rrf_score"),
        "best_vector_score": latest_check.get("best_vector_score"),
    }

    return InvestigationResponse(
        investigation_id=investigation.id,
        repository_name=repository.name if repository is not None else "",
        query=investigation.query,
        diagnosis=investigation.response or "INSUFFICIENT_EVIDENCE",
        confidence=investigation.confidence or "low",
        raw_confidence=None,
        cited_chunk_ids=[str(item) for item in audit_payload.get("cited_chunk_ids", [])],
        evidence_check=evidence_check,
        retry_used=any(attempt.get("stage") == "widened_retry" for attempt in tool_calls),
        tool_calls=tool_calls,
        model=investigation.model or "",
        latency_ms=investigation.latency_ms,
        evaluation_note=EVALUATION_NOTE,
    )


@router.get(
    "/repositories",
    response_model=list[RepositorySummary],
    dependencies=[Depends(require_api_access)],
)
async def list_repositories() -> list[RepositorySummary]:
    """List repositories and their total/embedded chunk counts."""

    async with AsyncSessionLocal() as session:
        rows = (
            await session.execute(
                select(
                    Repository.name,
                    func.count(Chunk.id),
                    func.count(Chunk.embedding),
                )
                .outerjoin(Chunk, Chunk.repository_id == Repository.id)
                .group_by(Repository.id, Repository.name)
                .order_by(Repository.name)
            )
        ).all()

    return [
        RepositorySummary(
            name=name,
            chunk_count=int(chunk_count),
            embedded_chunk_count=int(embedded_count),
        )
        for name, chunk_count, embedded_count in rows
    ]