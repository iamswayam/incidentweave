"""Local MCP server exposing IncidentWeave retrieval tools."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP
from sqlalchemy import select

from app.db.models import Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.hybrid_search import hybrid_search
from scripts.ingest_repo import iter_python_files

server = FastMCP("IncidentWeave local investigation tools")


def grep_search(
    repository_path: str | Path,
    keyword: str,
    repository_id: int,
    limit: int = 20,
) -> list[dict[str, object]]:
    """Find case-insensitive literal matches in ingester-visible Python files."""

    if not keyword:
        raise ValueError("keyword must not be empty")
    if limit <= 0:
        return []

    root = Path(repository_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"Repository path is not a directory: {repository_path}")

    needle = keyword.casefold()
    matches: list[dict[str, object]] = []
    for file_path in sorted(iter_python_files(root)):
        relative_path = file_path.relative_to(root).as_posix()
        lines = file_path.read_text(encoding="utf-8", errors="replace").splitlines()
        for line_number, line in enumerate(lines, start=1):
            if needle not in line.casefold():
                continue
            matches.append(
                {
                    "id": f"grep-{len(matches) + 1}",
                    "repository_id": repository_id,
                    "file_path": relative_path,
                    "line_start": line_number,
                    "line_end": line_number,
                    "content": line,
                    "vector_score": None,
                    "fts_score": None,
                    "rrf_score": None,
                }
            )
            if len(matches) >= limit:
                return matches
    return matches


@server.tool(
    name="hybrid_search",
    description="Search one indexed repository with vector and PostgreSQL full-text retrieval.",
)
async def hybrid_search_tool(
    repository_name: str,
    query_text: str,
    query_embedding: list[float],
    limit: int = 10,
) -> str:
    """Call the existing hybrid search implementation for a repository."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        results = await hybrid_search(
            session,
            repository.id,
            query_text,
            query_embedding,
            limit=limit,
        )
    return json.dumps(results)


@server.tool(
    name="grep_search",
    description=(
        "Find a literal keyword in Python source files under a local repository path; "
        "uses the same file and directory exclusions as ingestion."
    ),
)
async def grep_search_tool(
    repository_name: str,
    repository_path: str,
    keyword: str,
    limit: int = 20,
) -> str:
    """Resolve the repository ID and search its raw local Python sources."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repository_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repository_name}")
        matches = grep_search(
            repository_path,
            keyword,
            repository.id,
            limit=limit,
        )
    return json.dumps(matches)


def main() -> None:
    """Run the MCP server over stdio."""

    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
