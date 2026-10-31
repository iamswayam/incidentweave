"""Run the full investigation pipeline for a repository query."""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path
from time import perf_counter
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
    GENERATION_UNAVAILABLE_ERROR_CLASSES,
    MAX_GENERATION_ATTEMPTS,
    generation_failure_trace,
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
from app.investigation.parsing import (  # noqa: E402
    ModelOutputError,
    extract_generation_trace,
)
from app.investigation.persistence import (  # noqa: E402
    OUTCOME_ABSTAINED_MODEL,
    OUTCOME_ANSWERED,
    OUTCOME_EMBEDDING_UNAVAILABLE,
    OUTCOME_GENERATION_UNAVAILABLE,
    OUTCOME_REFUSED_GUARD,
    content_free_tool_call_trace,
    latest_ingest_run_id,
    persist_degraded_investigation,
    persist_error,
    persist_generation_unavailable,
    persist_investigation,
    persist_refusal,
)
from app.investigation.prompt import PROMPT_VERSION  # noqa: E402
from app.investigation.replay import ReplayRecord, build_chunk_records  # noqa: E402
from app.providers.gemini import ProviderError  # noqa: E402
from app.providers.usage import correlation_id_var  # noqa: E402
from app.retrieval.degraded_search import search_degraded_lexical_only  # noqa: E402
from app.retrieval.query_embedding_cache import (  # noqa: E402
    QueryEmbeddingKey,
    build_query_embedding_key,
    get_query_embedding,
    put_query_embedding,
)
from scripts.embed_chunks import (  # noqa: E402
    EMBEDDING_DIMENSION,
    GEMINI_MODEL,
    MAX_EMBEDDING_ATTEMPTS,
    embed_text,
)

INVESTIGATION_DEADLINE_SECONDS = 120
QUERY_EMBEDDING_TASK_TYPE = "default"
_logger = logging.getLogger(__name__)


def _content_free_evidence(
    retrieval_results: list[dict[str, object]],
) -> list[dict[str, object]]:
    return [
        {
            "chunk_id": str(item.get("id") or ""),
            "file_path": str(item.get("file_path") or ""),
            "start_line": item.get("line_start"),
            "end_line": item.get("line_end"),
            "rank": rank,
            "rrf_score": item.get("rrf_score"),
            "vector_score": item.get("vector_score"),
        }
        for rank, item in enumerate(retrieval_results, start=1)
    ]


def _query_embedding_failure_trace(
    error: Exception,
    *,
    elapsed_ms: int,
    correlation_id: str,
    cache_key: QueryEmbeddingKey,
    retrieval_mode: str,
    result_count: int,
) -> dict[str, object]:
    error_class = error.error_class if isinstance(error, ProviderError) else type(error).__name__
    attempt_count = (
        0
        if isinstance(error, ProviderError)
        and error.error_class == "rate_limited"
        and error.status_code is None
        else (
            MAX_EMBEDDING_ATTEMPTS
            if isinstance(error, ProviderError) and error.retryable
            else 1
        )
    )
    return {
        "failed_stage": "query_embedding",
        "model": GEMINI_MODEL,
        "provider_attempts": [
            {
                "provider": "gemini",
                "model": GEMINI_MODEL,
                "error_class": error_class,
                "attempt_count": attempt_count,
                "attempt_count_basis": "inferred_from_error_class",
            }
        ],
        "error_classes": [error_class],
        "attempt_count": attempt_count,
        "attempt_count_basis": "inferred_from_error_class",
        "elapsed_ms": elapsed_ms,
        "correlation_id": correlation_id,
        "cache": {
            "hit": False,
            "miss": True,
            "embedding_model": cache_key.embedding_model,
            "task_type": cache_key.task_type,
            "dimensions": cache_key.dimensions,
            "query_hash": cache_key.query_hash,
        },
        "retrieval_mode": retrieval_mode,
        "result_count": result_count,
        "guard_ran": False,
    }


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


async def _lookup_query_embedding_cache(
    key: QueryEmbeddingKey,
) -> tuple[list[float] | None, bool]:
    try:
        async with AsyncSessionLocal() as session:
            vector = await get_query_embedding(session, key)
            await session.commit()
        return vector, True
    except Exception as exc:
        _logger.warning("Query embedding cache read failed (%s)", type(exc).__name__)
        return None, False


async def _store_query_embedding_cache(
    key: QueryEmbeddingKey,
    vector: list[float],
) -> None:
    try:
        async with AsyncSessionLocal() as session:
            await put_query_embedding(session, key, vector)
            await session.commit()
    except Exception as exc:
        _logger.warning("Query embedding cache write failed (%s)", type(exc).__name__)


def _query_embedding_cache_trace(
    key: QueryEmbeddingKey,
    *,
    hit: bool,
    lookup_succeeded: bool = True,
) -> dict[str, object]:
    return {
        "hit": hit,
        "miss": lookup_succeeded and not hit,
        "lookup_succeeded": lookup_succeeded,
        "embedding_model": key.embedding_model,
        "task_type": key.task_type,
        "dimensions": key.dimensions,
        "query_hash": key.query_hash,
    }


async def investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
    persist: bool = True,
    *,
    temperature: float | None = None,
) -> dict[str, object]:
    """Run an investigation with a stable provider-usage correlation ID."""

    correlation_id = uuid4().hex
    token = correlation_id_var.set(correlation_id)
    try:
        return await _investigate_repository(
            repo_name,
            query_text,
            limit,
            persist,
            temperature=temperature,
            correlation_id=correlation_id,
        )
    finally:
        correlation_id_var.reset(token)


async def _investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
    persist: bool = True,
    *,
    temperature: float | None = None,
    correlation_id: str,
) -> dict[str, object]:
    """Perform the end-to-end grounded investigation flow for one query."""

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

    stage = "query_embedding"
    stage_started_at = perf_counter()
    cache_key = build_query_embedding_key(
        GEMINI_MODEL,
        QUERY_EMBEDDING_TASK_TYPE,
        EMBEDDING_DIMENSION,
        query_text,
    )
    cache_vector: list[float] | None = None
    cache_checked = False
    cache_hit = False
    cache_trace = _query_embedding_cache_trace(cache_key, hit=False)
    embedding_failure: ProviderError | None = None
    result: dict[str, object]
    try:
        async with asyncio.timeout(INVESTIGATION_DEADLINE_SECONDS):
            cache_vector, cache_checked = await _lookup_query_embedding_cache(cache_key)
            cache_hit = cache_vector is not None
            cache_trace = _query_embedding_cache_trace(
                cache_key,
                hit=cache_hit,
                lookup_succeeded=cache_checked,
            )
            if cache_hit:
                query_embedding = cache_vector
            else:
                try:
                    query_embedding = await embed_text(query_text)
                except ProviderError as exc:
                    if (
                        cache_checked
                        and exc.error_class in GENERATION_UNAVAILABLE_ERROR_CLASSES
                    ):
                        embedding_failure = exc
                        stage = "lexical_retrieval"
                        async with AsyncSessionLocal() as session:
                            retrieval_results = await search_degraded_lexical_only(
                                session,
                                repository_id,
                                query_text,
                                limit,
                            )
                    else:
                        raise
                else:
                    await _store_query_embedding_cache(cache_key, query_embedding)

            if embedding_failure is not None:
                elapsed_ms = round((perf_counter() - stage_started_at) * 1000)
                failure_trace = _query_embedding_failure_trace(
                    embedding_failure,
                    elapsed_ms=elapsed_ms,
                    correlation_id=correlation_id,
                    cache_key=cache_key,
                    retrieval_mode="lexical_only",
                    result_count=len(retrieval_results),
                )
                failure_trace["cache"] = cache_trace
                result = {
                    "outcome": OUTCOME_EMBEDDING_UNAVAILABLE,
                    "unavailable_answer": True,
                    "degraded": True,
                    "degraded_reason": "embedding_unavailable",
                    "diagnosis": "",
                    "confidence": "not_applicable",
                    "cited_chunk_ids": [],
                    "claims": [],
                    "uncertainty_note": (
                        "Lexical-only evidence is returned; the vector guard and "
                        "generation were not run."
                    ),
                    "retrieval_results": retrieval_results,
                    "retrieved_before_budget": retrieval_results,
                    "evidence_check": {
                        "is_sufficient": None,
                        "reason": "not evaluated: no query embedding",
                        "best_rrf_score": None,
                        "best_vector_score": None,
                    },
                    "retry_used": False,
                    "confidence_calibrated": False,
                    "calibration_note": "",
                    "model": "",
                    "latency_ms": None,
                    "tool_calls": [
                        {
                            "tool": "degraded_lexical_search",
                            "stage": "lexical_only",
                            "parameters": {"limit": limit},
                            "outcome": {"result_count": len(retrieval_results)},
                        }
                    ],
                    "generation_trace": failure_trace,
                }
            else:
                stage = "investigation"
                stage_started_at = perf_counter()
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
                        "temperature": temperature,
                    }
                )
    except Exception as exc:
        elapsed_ms = round((perf_counter() - stage_started_at) * 1000)
        if stage == "query_embedding":
            error_trace = _query_embedding_failure_trace(
                exc,
                elapsed_ms=elapsed_ms,
                correlation_id=correlation_id,
                cache_key=cache_key,
                retrieval_mode="hybrid",
                result_count=0,
            )
            error_trace["cache"] = cache_trace
        elif stage == "investigation" and isinstance(
            exc, (ProviderError, TimeoutError)
        ):
            error_trace = generation_failure_trace(exc, elapsed_ms=elapsed_ms)
            error_trace["cache"] = cache_trace
        elif isinstance(exc, ModelOutputError):
            error_trace = {
                "failed_stage": "generation",
                "model": GEMINI_GENERATION_MODEL,
                "provider_attempts": [
                    {
                        "provider": "gemini",
                        "model": GEMINI_GENERATION_MODEL,
                        "error_class": "schema_invalid",
                        "attempt_count": 1,
                        "attempt_count_basis": "inferred_from_error_class",
                    }
                ],
                "error_classes": ["schema_invalid"],
                "attempt_count": 1,
                "attempt_count_basis": "inferred_from_error_class",
                "elapsed_ms": elapsed_ms,
                "correlation_id": correlation_id,
                "cache": cache_trace,
            }
        else:
            error_trace = {
                "failed_stage": stage,
                "provider_attempts": [],
                "error_classes": [type(exc).__name__],
                "attempt_count": 0,
                "elapsed_ms": elapsed_ms,
                "correlation_id": correlation_id,
            }
        if error_trace.get("failed_stage") not in {"query_embedding", "generation"}:
            error_trace["model"] = None
        elif stage == "query_embedding":
            error_trace["model"] = GEMINI_MODEL
        if persist:
            try:
                async with AsyncSessionLocal() as session:
                    await persist_error(
                        session,
                        repository_id,
                        query_text,
                        type(exc).__name__,
                        ingest_run_id=ingest_run_id,
                        replay=ReplayRecord(trace={"outcome": "error", **error_trace}),
                    )
            except Exception as persistence_error:
                print(
                    "Failed to persist investigation error "
                    f"({type(persistence_error).__name__})",
                    file=sys.stderr,
                )
        raise

    if result.get("outcome") == OUTCOME_EMBEDDING_UNAVAILABLE:
        retrieval_results = result["retrieval_results"]
        evidence = _content_free_evidence(retrieval_results)
        failure_trace = result["generation_trace"]
        tool_call_trace = content_free_tool_call_trace(result["tool_calls"])
        replay = ReplayRecord(
            embedding_model=GEMINI_MODEL,
            chunk_records=build_chunk_records(retrieval_results, []),
            trace={
                **failure_trace,
                "outcome": OUTCOME_EMBEDDING_UNAVAILABLE,
                "degraded": True,
                "degraded_reason": "embedding_unavailable",
            },
        )
        if persist:
            async with AsyncSessionLocal() as session:
                investigation = await persist_degraded_investigation(
                    session=session,
                    repository_id=repository_id,
                    query=query_text,
                    retrieval_results=retrieval_results,
                    evidence=evidence,
                    evidence_check=result["evidence_check"],
                    tool_call_trace=tool_call_trace,
                    generation_trace=replay.trace or failure_trace,
                    outcome=OUTCOME_EMBEDDING_UNAVAILABLE,
                    degraded_reason="embedding_unavailable",
                    uncertainty_note=str(result["uncertainty_note"]),
                    ingest_run_id=ingest_run_id,
                    replay=replay,
                )
            investigation_id = investigation.id
        return {
            "repository": repo_name,
            "investigation_id": investigation_id,
            "query": query_text,
            "diagnosis": "",
            "confidence": "not_applicable",
            "outcome": OUTCOME_EMBEDDING_UNAVAILABLE,
            "unavailable_answer": True,
            "degraded": True,
            "degraded_reason": "embedding_unavailable",
            "evidence": evidence,
            "cited_chunk_ids": [],
            "retrieval_results": retrieval_results,
            "evidence_check": result["evidence_check"],
            "model": "",
            "latency_ms": None,
            "retry_used": False,
            "confidence_calibrated": False,
            "calibration_note": "",
            "tool_calls": tool_call_trace,
            "claims": [],
            "uncertainty_note": result["uncertainty_note"],
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
            "generation_trace": failure_trace,
        }

    if result.get("outcome") == OUTCOME_GENERATION_UNAVAILABLE:
        retrieval_results = result.get(
            "retrieved_before_budget",
            result["retrieval_results"],
        )
        kept_chunk_ids = [
            item.get("id")
            for item in result["retrieval_results"]
            if item.get("id") is not None
        ]
        evidence = _content_free_evidence(retrieval_results)
        generation_trace = {
            **result["generation_trace"],
            "cache": cache_trace,
        }
        tool_call_trace = content_free_tool_call_trace(result["tool_calls"])
        replay = ReplayRecord(
            thresholds=_current_thresholds(),
            embedding_model=GEMINI_MODEL,
            chunk_records=build_chunk_records(
                retrieval_results,
                kept_chunk_ids,
            ),
            trace={
                **generation_trace,
                "outcome": OUTCOME_GENERATION_UNAVAILABLE,
                "degraded": True,
                "degraded_reason": "generation_unavailable",
                "cache": cache_trace,
            },
        )
        if persist:
            async with AsyncSessionLocal() as session:
                investigation = await persist_generation_unavailable(
                    session=session,
                    repository_id=repository_id,
                    query=query_text,
                    retrieval_results=retrieval_results,
                    evidence=evidence,
                    evidence_check=result["evidence_check"],
                    tool_call_trace=tool_call_trace,
                    generation_trace=replay.trace or generation_trace,
                    ingest_run_id=ingest_run_id,
                    replay=replay,
                )
            investigation_id = investigation.id
        return {
            "repository": repo_name,
            "investigation_id": investigation_id,
            "query": query_text,
            "diagnosis": "",
            "confidence": "not_applicable",
            "outcome": OUTCOME_GENERATION_UNAVAILABLE,
            "unavailable_answer": True,
            "degraded": True,
            "degraded_reason": "generation_unavailable",
            "evidence": evidence,
            "cited_chunk_ids": [],
            "retrieval_results": retrieval_results,
            "evidence_check": result["evidence_check"],
            "model": "",
            "latency_ms": None,
            "retry_used": result["retry_used"],
            "confidence_calibrated": False,
            "calibration_note": "",
            "tool_calls": tool_call_trace,
            "claims": [],
            "uncertainty_note": result["uncertainty_note"],
            "citation_validation": {"submitted": 0, "valid": 0, "rate": None},
            "generation_trace": generation_trace,
        }

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
                "query_embedding_cache": cache_trace,
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
            "temperature": temperature,
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
            "query_embedding_cache": cache_trace,
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
                model=str(result["model"]),
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
        "model": result["model"],
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
    print(f"Outcome: {result['outcome']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Model self-rating: {result['confidence']}")
    print(f"Unavailable answer: {bool(result.get('unavailable_answer', False))}")
    print(f"Degraded: {bool(result.get('degraded', False))}")
    print(f"Degraded reason: {result.get('degraded_reason')}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; model self-rating calibrated: "
        f"{result['confidence_calibrated']}"
    )
    print(f"Tool attempts: {len(result['tool_calls'])}")
    generation_trace = result.get("generation_trace")
    if isinstance(generation_trace, dict):
        safe_trace = {
            key: value for key, value in generation_trace.items() if key != "raw_text"
        }
    else:
        safe_trace = generation_trace
    print(f"Generation trace: {json.dumps(safe_trace, sort_keys=True)}")
    evidence = result.get("evidence")
    if isinstance(evidence, list) and evidence:
        print(f"Evidence metadata: {json.dumps(evidence, sort_keys=True)}")


if __name__ == "__main__":
    main()
