"""Run the full investigation pipeline for a repository query."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from uuid import uuid4

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.models import Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.investigation.confidence import (  # noqa: E402
    MAX_CLEAR_VECTOR_DISTANCE,
    MIN_CLEAR_RRF_SCORE,
    calibrate_confidence,
)
from app.investigation.generation import (  # noqa: E402
    GEMINI_GENERATION_MODEL,
    GENERATION_TIMEOUT_SECONDS,
    MAX_GENERATION_ATTEMPTS,
)
from app.investigation.graph import create_investigation_graph  # noqa: E402
from app.investigation.guard import (  # noqa: E402
    MAX_ACCEPTABLE_VECTOR_DISTANCE,
    MIN_ACCEPTABLE_RRF_SCORE,
)
from app.investigation.limits import (  # noqa: E402
    MAX_EVIDENCE_CHARS,
    MAX_LIMIT,
    MAX_QUERY_CHARS,
)
from app.investigation.parsing import extract_generation_trace  # noqa: E402
from app.investigation.persistence import (  # noqa: E402
    OUTCOME_ABSTAINED_MODEL,
    OUTCOME_ANSWERED,
    OUTCOME_REFUSED_GUARD,
    latest_ingest_run_id,
    persist_error,
    persist_investigation,
    persist_refusal,
)
from app.investigation.prompt import PROMPT_VERSION  # noqa: E402
from app.investigation.replay import ReplayRecord, build_chunk_records  # noqa: E402
from scripts.embed_chunks import GEMINI_MODEL, embed_text  # noqa: E402

INVESTIGATION_DEADLINE_SECONDS = 120


def parse_args() -> argparse.Namespace:
    """Parse repository name and query from the CLI."""

    parser = argparse.ArgumentParser(
        description=(
            "Run retrieval, grounding, generation, parsing, and persistence "
            "for one repository query."
        )
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("query", help="Natural-language question to investigate")
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum hybrid-search results to consider",
    )
    return parser.parse_args()


async def investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
    persist: bool = True,
) -> dict[str, object]:
    """Perform the end-to-end grounded investigation flow for one query."""

    correlation_id = uuid4().hex
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"--limit must be between 1 and {MAX_LIMIT}")
    if len(query_text) > MAX_QUERY_CHARS:
        raise ValueError(f"--query must be at most {MAX_QUERY_CHARS} characters")

    investigation_id: int | None = None

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")
        repository_id = repository.id
        ingest_run_id = await latest_ingest_run_id(session, repository_id)

    try:
        async with asyncio.timeout(INVESTIGATION_DEADLINE_SECONDS):
            query_embedding = await embed_text(query_text)
            graph = create_investigation_graph(calibrate_confidence)
            result = await graph.ainvoke(
                {
                    "repository_id": repository_id,
                    "repository_name": repo_name,
                    "query": query_text,
                    "query_embedding": query_embedding,
                    "search_limit": limit,
                    "retry_limit": limit * 2,
                    "retry_count": 0,
                    "retry_used": False,
                    "retrieval_results": [],
                    "evidence_check": {},
                    "diagnosis": "",
                    "confidence": "",
                    "cited_chunk_ids": [],
                    "model": GEMINI_GENERATION_MODEL,
                    "latency_ms": None,
                    "calibration_note": "",
                    "confidence_calibrated": False,
                    "evidence_source": "hybrid",
                    "tool_calls": [],
                }
            )
    except Exception as exc:
        if persist:
            try:
                async with AsyncSessionLocal() as session:
                    await persist_error(
                        session,
                        repository_id,
                        query_text,
                        type(exc).__name__,
                        ingest_run_id=ingest_run_id,
                        replay=ReplayRecord(
                            trace={
                                "correlation_id": correlation_id,
                                "outcome": "error",
                                "model": GEMINI_GENERATION_MODEL,
                                "generation_latency_ms": None,
                                "error_class": type(exc).__name__,
                            }
                        ),
                    )
            except Exception as persistence_error:
                print(
                    "Failed to persist investigation error "
                    f"({type(persistence_error).__name__})",
                    file=sys.stderr,
                )
        raise

    if not result["evidence_check"]["is_sufficient"]:
        replay = ReplayRecord(
            thresholds=_current_thresholds(),
            embedding_model=GEMINI_MODEL,
            chunk_records=build_chunk_records(
                result.get("retrieved_before_budget", result["retrieval_results"]),
                [],
            ),
            trace={
                "correlation_id": correlation_id,
                "outcome": OUTCOME_REFUSED_GUARD,
                "model": None,
                "generation_latency_ms": None,
                "error_class": None,
            },
        )
        if persist:
            async with AsyncSessionLocal() as session:
                investigation = await persist_refusal(
                    session,
                    repository_id,
                    query_text,
                    result["retrieval_results"],
                    result["tool_calls"],
                    ingest_run_id=ingest_run_id,
                    replay=replay,
                )
            investigation_id = investigation.id
        return {
            "repository": repo_name,
            "investigation_id": investigation_id,
            "query": query_text,
            "diagnosis": result["diagnosis"],
            "confidence": result["confidence"],
            "outcome": OUTCOME_REFUSED_GUARD,
            "cited_chunk_ids": result["cited_chunk_ids"],
            "retrieval_results": result["retrieval_results"],
            "evidence_check": result["evidence_check"],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "retry_used": result["retry_used"],
            "confidence_calibrated": result["confidence_calibrated"],
            "calibration_note": result["calibration_note"],
            "tool_calls": result["tool_calls"],
            "claims": [],
            "uncertainty_note": result["evidence_check"]["reason"],
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
            "generation_trace": extract_generation_trace(
                result.get("prompt"), result.get("response_payload")
            ),
        }

    investigation_response = result["diagnosis"]
    investigation_confidence = result["confidence"]
    outcome = (
        OUTCOME_ABSTAINED_MODEL
        if str(result["diagnosis"]).rstrip(".").strip().upper() == "INSUFFICIENT_EVIDENCE"
        else OUTCOME_ANSWERED
    )
    replay = ReplayRecord(
        prompt=str(result.get("prompt") or ""),
        prompt_version=PROMPT_VERSION,
        raw_response=str(result.get("raw_response") or ""),
        raw_self_rating=str(result.get("raw_self_rating") or ""),
        generation_params={
            "timeout_seconds": GENERATION_TIMEOUT_SECONDS,
            "max_attempts": MAX_GENERATION_ATTEMPTS,
            "response_mime_type": "application/json",
            "response_schema_version": "grounded-v3",
        },
        thresholds=_current_thresholds(),
        embedding_model=GEMINI_MODEL,
        chunk_records=build_chunk_records(
            result.get("retrieved_before_budget", result["retrieval_results"]),
            [
                item.get("id")
                for item in result["retrieval_results"]
                if item.get("id") is not None
            ],
        ),
        trace={
            "correlation_id": correlation_id,
            "outcome": outcome,
            "model": result["model"],
            "generation_latency_ms": result["latency_ms"],
            "error_class": None,
        },
    )
    if persist:
        response_payload = result["response_payload"]
        async with AsyncSessionLocal() as session:
            investigation = await persist_investigation(
                session=session,
                repository_id=repository_id,
                query=query_text,
                response_payload=response_payload,
                retrieval_results=result["retrieval_results"],
                model=GEMINI_GENERATION_MODEL,
                latency_ms=result["latency_ms"],
                final_confidence=result["confidence"],
                token_usage=(
                    response_payload.get("usageMetadata", {}).get("totalTokenCount")
                    if isinstance(response_payload.get("usageMetadata"), dict)
                    else None
                ),
                tool_call_trace=result["tool_calls"],
                ingest_run_id=ingest_run_id,
                replay=replay,
            )
        investigation_response = investigation.response
        investigation_confidence = investigation.confidence
        investigation_id = investigation.id

    return {
        "repository": repo_name,
        "investigation_id": investigation_id,
        "query": query_text,
        "diagnosis": result["diagnosis"] or investigation_response,
        "confidence": result["confidence"] or investigation_confidence,
        "outcome": outcome,
        "cited_chunk_ids": result["cited_chunk_ids"],
        "retrieval_results": result["retrieval_results"],
        "evidence_check": result["evidence_check"],
        "model": GEMINI_GENERATION_MODEL,
        "latency_ms": result["latency_ms"],
        "retry_used": result["retry_used"],
        "confidence_calibrated": result["confidence_calibrated"],
        "calibration_note": result["calibration_note"],
        "tool_calls": result["tool_calls"],
        "claims": result.get("claims", []),
        "uncertainty_note": result.get("uncertainty_note", ""),
        "citation_validation": {
            "submitted": result.get("submitted_citation_count", 0),
            "valid": result.get("valid_citation_count", 0),
            "rate": result.get("citation_validity_rate"),
        },
        "generation_trace": extract_generation_trace(
            result.get("prompt"), result.get("response_payload")
        ),
    }


def _current_thresholds() -> dict[str, object]:
    return {
        "max_acceptable_vector_distance": MAX_ACCEPTABLE_VECTOR_DISTANCE,
        "min_acceptable_rrf_score": MIN_ACCEPTABLE_RRF_SCORE,
        "max_clear_vector_distance": MAX_CLEAR_VECTOR_DISTANCE,
        "min_clear_rrf_score": MIN_CLEAR_RRF_SCORE,
        "max_evidence_chars": MAX_EVIDENCE_CHARS,
        "max_limit": MAX_LIMIT,
        "max_query_chars": MAX_QUERY_CHARS,
    }


def main() -> None:
    """Run the investigation CLI and print a concise result."""

    args = parse_args()

    try:
        result = asyncio.run(
            investigate_repository(
                args.repo_name,
                args.query,
                limit=args.limit,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Model self-rating: {result['confidence']}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; model self-rating calibrated: "
        f"{result['confidence_calibrated']}"
    )
    print(f"Tool attempts: {len(result['tool_calls'])}")


if __name__ == "__main__":
    main()
