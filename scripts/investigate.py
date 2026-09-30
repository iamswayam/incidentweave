"""Run the full investigation pipeline for a repository query."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from sqlalchemy import select  # noqa: E402

from app.db.models import Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.investigation.confidence import calibrate_confidence  # noqa: E402
from app.investigation.generation import GEMINI_GENERATION_MODEL  # noqa: E402
from app.investigation.graph import create_investigation_graph  # noqa: E402
from app.investigation.persistence import persist_investigation  # noqa: E402
from scripts.embed_chunks import embed_text  # noqa: E402


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
    parser.add_argument(
        "--repo-path",
        default=str(REPO_ROOT),
        help="Local repository root used by the literal grep fallback",
    )
    return parser.parse_args()


async def investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
    repo_path: str = str(REPO_ROOT),
    persist: bool = True,
) -> dict[str, object]:
    """Perform the end-to-end grounded investigation flow for one query."""

    if limit <= 0:
        raise ValueError("--limit must be greater than zero")

    investigation_id: int | None = None

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")
        repository_id = repository.id

    query_embedding = embed_text(query_text)
    graph = create_investigation_graph(calibrate_confidence)
    result = await graph.ainvoke(
        {
            "repository_id": repository_id,
            "repository_name": repo_name,
            "repository_path": str(Path(repo_path).resolve()),
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

    if not result["evidence_check"]["is_sufficient"]:
        return {
            "repository": repo_name,
            "investigation_id": None,
            "query": query_text,
            "diagnosis": result["diagnosis"],
            "confidence": result["confidence"],
            "cited_chunk_ids": result["cited_chunk_ids"],
            "retrieval_results": result["retrieval_results"],
            "evidence_check": result["evidence_check"],
            "model": result["model"],
            "latency_ms": result["latency_ms"],
            "retry_used": result["retry_used"],
            "confidence_calibrated": result["confidence_calibrated"],
            "calibration_note": result["calibration_note"],
            "tool_calls": result["tool_calls"],
        }

    investigation_response = result["diagnosis"]
    investigation_confidence = result["confidence"]
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
        "cited_chunk_ids": result["cited_chunk_ids"],
        "retrieval_results": result["retrieval_results"],
        "evidence_check": result["evidence_check"],
        "model": GEMINI_GENERATION_MODEL,
        "latency_ms": result["latency_ms"],
        "retry_used": result["retry_used"],
        "confidence_calibrated": result["confidence_calibrated"],
        "calibration_note": result["calibration_note"],
        "tool_calls": result["tool_calls"],
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
                repo_path=args.repo_path,
            )
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")
    print(f"Diagnosis: {result['diagnosis']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Cited chunks: {result['cited_chunk_ids']}")
    print(f"Model: {result['model']}")
    print(f"Latency ms: {result['latency_ms']}")
    print(
        "Retry used: "
        f"{result['retry_used']}; confidence calibrated: "
        f"{result['confidence_calibrated']}"
    )
    print(f"Tool attempts: {len(result['tool_calls'])}")


if __name__ == "__main__":
    main()
