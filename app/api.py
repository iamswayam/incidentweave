"""HTTP routes for persisted investigations and repository summaries."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api_security import require_api_access
from app.db.models import Audit, Chunk, Investigation, Repository
from app.db.session import AsyncSessionLocal
from app.investigation.limits import MAX_LIMIT, MAX_QUERY_CHARS
from scripts.investigate import investigate_repository

router = APIRouter()

EVALUATION_NOTE = (
    "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only "
    "(hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, "
    "and no tested vector-distance cutoff separated the groups. These results are "
    "diagnostic, not a benchmark; see docs/phases/08-evaluation.md for limits."
)
RATING_NOTE = (
    "Model self-rating (low, medium or high). It is the model's own label, lowered when "
    "retrieval scores are weak. It is not a measured probability of correctness; no "
    "accuracy check exists yet."
)


class InvestigationRequest(BaseModel):
    """Input for one synchronous grounded investigation."""

    repository_name: str = Field(min_length=1, max_length=255)
    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    limit: int = Field(default=5, ge=1, le=MAX_LIMIT)


class InvestigationEvidence(BaseModel):
    """Content-free location and ranking metadata for retrieved evidence."""

    chunk_id: str
    file_path: str
    start_line: int | None
    end_line: int | None
    rank: int
    rrf_score: float | None
    vector_score: float | None


class InvestigationResponse(BaseModel):
    """Investigation output with the model's self-rating and its limitations."""

    investigation_id: int | None
    repository_name: str
    query: str
    diagnosis: str
    outcome: str
    model_self_rating: str
    rating_note: str
    cited_chunk_ids: list[str]
    evidence_check: dict[str, Any]
    retry_used: bool
    tool_calls: list[dict[str, Any]]
    claims: list[dict[str, Any]] = Field(default_factory=list)
    uncertainty_note: str = ""
    citation_validation: dict[str, Any] = Field(default_factory=dict)
    model: str
    latency_ms: int | None
    evaluation_note: str
    unavailable_answer: bool = False
    degraded: bool = False
    degraded_reason: str | None = None
    evidence: list[InvestigationEvidence] = Field(default_factory=list)


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
    except (RuntimeError, TimeoutError) as exc:
        raise _http_error(
            502,
            "upstream_failure",
            "The investigation provider failed after its retries.",
        ) from exc

    calibration_note = str(result.get("calibration_note") or "")
    evidence_check = result.get("evidence_check")
    if not isinstance(evidence_check, dict):
        evidence_check = {}
    tool_calls = result.get("tool_calls")
    if not isinstance(tool_calls, list):
        tool_calls = []
    cited_chunk_ids = result.get("cited_chunk_ids")
    if not isinstance(cited_chunk_ids, list):
        cited_chunk_ids = []
    unavailable_answer = result.get("unavailable_answer") is True
    evidence = result.get("evidence")
    if not isinstance(evidence, list):
        evidence = []

    return InvestigationResponse(
        investigation_id=(
            int(result["investigation_id"])
            if isinstance(result.get("investigation_id"), int)
            else None
        ),
        repository_name=str(result.get("repository") or payload.repository_name),
        query=str(result.get("query") or payload.query),
        diagnosis=(
            ""
            if unavailable_answer
            else str(result.get("diagnosis") or "INSUFFICIENT_EVIDENCE")
        ),
        outcome=str(result["outcome"]),
        model_self_rating=(
            "not_applicable"
            if unavailable_answer
            else str(result.get("confidence") or "low")
        ),
        rating_note=(
            "No model response was generated."
            if unavailable_answer
            else (
                f"{RATING_NOTE} {calibration_note}"
                if calibration_note
                else RATING_NOTE
            )
        ),
        cited_chunk_ids=[str(chunk_id) for chunk_id in cited_chunk_ids],
        evidence_check=evidence_check,
        retry_used=bool(result.get("retry_used")),
        tool_calls=tool_calls,
        claims=[
            claim for claim in result.get("claims", []) if isinstance(claim, dict)
        ],
        uncertainty_note=str(result.get("uncertainty_note") or ""),
        citation_validation=(
            result.get("citation_validation")
            if isinstance(result.get("citation_validation"), dict)
            else {"submitted": 0, "valid": 0, "rate": None}
        ),
        model=str(result.get("model") or ""),
        latency_ms=(
            int(result["latency_ms"])
            if isinstance(result.get("latency_ms"), int)
            else None
        ),
        evaluation_note=EVALUATION_NOTE,
        unavailable_answer=unavailable_answer,
        degraded=result.get("degraded") is True,
        degraded_reason=(
            str(result["degraded_reason"])
            if isinstance(result.get("degraded_reason"), str)
            else None
        ),
        evidence=evidence,
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
    citation_validation = audit_payload.get("citation_validation")
    if not isinstance(citation_validation, dict):
        citation_validation = {"submitted": 0, "valid": 0, "rate": None}
    degraded_payload = audit_payload.get("degraded")
    if not isinstance(degraded_payload, dict):
        degraded_payload = {}
    stored_evidence_check = degraded_payload.get("evidence_check")
    if isinstance(stored_evidence_check, dict):
        evidence_check = {
            "is_sufficient": stored_evidence_check.get("is_sufficient"),
            "reason": stored_evidence_check.get("reason"),
            "best_rrf_score": stored_evidence_check.get("best_rrf_score"),
            "best_vector_score": stored_evidence_check.get("best_vector_score"),
        }
    stored_evidence = degraded_payload.get("evidence")
    if not isinstance(stored_evidence, list):
        stored_evidence = []
    unavailable_answer = degraded_payload.get("unavailable_answer") is True

    return InvestigationResponse(
        investigation_id=investigation.id,
        repository_name=repository.name if repository is not None else "",
        query=investigation.query,
        diagnosis=(
            ""
            if unavailable_answer
            else investigation.response or "INSUFFICIENT_EVIDENCE"
        ),
        outcome=investigation.outcome,
        model_self_rating=(
            "not_applicable"
            if unavailable_answer
            else investigation.confidence or "low"
        ),
        rating_note=(
            "No model response was generated."
            if unavailable_answer
            else RATING_NOTE
        ),
        cited_chunk_ids=[str(item) for item in audit_payload.get("cited_chunk_ids", [])],
        evidence_check=evidence_check,
        retry_used=any(attempt.get("stage") == "widened_retry" for attempt in tool_calls),
        tool_calls=tool_calls,
        claims=[claim for claim in audit_payload.get("claims", []) if isinstance(claim, dict)],
        uncertainty_note=str(audit_payload.get("uncertainty_note") or ""),
        citation_validation=citation_validation,
        model=investigation.model or "",
        latency_ms=investigation.latency_ms,
        evaluation_note=EVALUATION_NOTE,
        unavailable_answer=unavailable_answer,
        degraded=degraded_payload.get("degraded") is True,
        degraded_reason=(
            str(degraded_payload["degraded_reason"])
            if isinstance(degraded_payload.get("degraded_reason"), str)
            else None
        ),
        evidence=stored_evidence,
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