"""Search repository chunks with hybrid vector and full-text retrieval."""

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
from app.retrieval.hybrid_search import hybrid_search  # noqa: E402
from scripts.embed_chunks import embed_text  # noqa: E402


def parse_args() -> argparse.Namespace:
    """Parse the repository name and natural-language query."""

    parser = argparse.ArgumentParser(
        description="Search repository chunks using Gemini embeddings and hybrid retrieval."
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("query", help="Natural-language question about the repository code")
    parser.add_argument("--limit", type=int, default=5, help="Maximum number of results")
    return parser.parse_args()


async def search_repository(
    repo_name: str,
    query_text: str,
    query_embedding: list[float],
    limit: int,
) -> list[dict[str, object]]:
    """Run hybrid search against the named repository."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        return await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )


def main() -> None:
    """Embed the query and print its top hybrid-search results."""

    args = parse_args()
    if args.limit <= 0:
        raise SystemExit("--limit must be greater than zero")

    try:
        query_embedding = embed_text(args.query)
        results = asyncio.run(
            search_repository(args.repo_name, args.query, query_embedding, args.limit)
        )
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc

    print(f"Repository: {args.repo_name}")
    print(f"Query: {args.query}")
    if not results:
        print("No matching chunks found.")
        return

    for rank, result in enumerate(results, start=1):
        content = " ".join(str(result.get("content") or "").split())
        if len(content) > 220:
            content = f"{content[:217]}..."
        print(
            f"{rank}. {result.get('file_path')}:{result.get('line_start')}-"
            f"{result.get('line_end')} rrf={result.get('rrf_score'):.6f}"
        )
        print(f"   {content}")


if __name__ == "__main__":
    main()
