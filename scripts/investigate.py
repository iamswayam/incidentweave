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
from app.investigation.generation import (  # noqa: E402
    GEMINI_GENERATION_MODEL,
    generate_investigation,
)
from app.investigation.guard import evaluate_evidence_sufficiency  # noqa: E402
from app.investigation.parsing import parse_investigation_response  # noqa: E402
from app.investigation.persistence import persist_investigation  # noqa: E402
from app.investigation.prompt import build_grounded_prompt  # noqa: E402
from app.retrieval.hybrid_search import hybrid_search  # noqa: E402
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
    return parser.parse_args()


async def investigate_repository(
    repo_name: str,
    query_text: str,
    limit: int = 5,
) -> dict[str, object]:
    """Perform the end-to-end grounded investigation flow for one query."""

    if limit <= 0:
        raise ValueError("--limit must be greater than zero")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        query_embedding = embed_text(query_text)
        retrieval_results = await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )

        evidence_check = evaluate_evidence_sufficiency(retrieval_results)
        if not evidence_check["is_sufficient"]:
            return {
                "repository": repo_name,
                "query": query_text,
                "diagnosis": "INSUFFICIENT_EVIDENCE",
                "confidence": "low",
                "cited_chunk_ids": [],
                "retrieval_results": retrieval_results,
                "evidence_check": evidence_check,
                "model": GEMINI_GENERATION_MODEL,
                "latency_ms": None,
            }

        prompt = build_grounded_prompt(query_text, retrieval_results)
        response_payload, latency_ms = generate_investigation(prompt)
        parsed = parse_investigation_response(response_payload, retrieval_results)
        investigation = await persist_investigation(
            session=session,
            repository_id=repository.id,
            query=query_text,
            response_payload=response_payload,
            retrieval_results=retrieval_results,
            model=GEMINI_GENERATION_MODEL,
            latency_ms=latency_ms,
            token_usage=(
                response_payload.get("usageMetadata", {}).get("totalTokenCount")
                if isinstance(response_payload.get("usageMetadata"), dict)
                else None
            ),
        )

        return {
            "repository": repo_name,
            "query": query_text,
            "diagnosis": parsed.get("diagnosis") or investigation.response,
            "confidence": parsed.get("confidence") or investigation.confidence,
            "cited_chunk_ids": parsed.get("cited_chunk_ids", []),
            "retrieval_results": retrieval_results,
            "evidence_check": evidence_check,
            "model": GEMINI_GENERATION_MODEL,
            "latency_ms": latency_ms,
        }


def main() -> None:
    """Run the investigation CLI and print a concise result."""

    args = parse_args()

    try:
        result = asyncio.run(investigate_repository(args.repo_name, args.query, limit=args.limit))
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


if __name__ == "__main__":
    main()
