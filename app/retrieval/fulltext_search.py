"""Full-text search over repository chunks."""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def search_fulltext(
    session: AsyncSession,
    repository_id: int,
    query_text: str,
    limit: int = 10,
) -> list[dict[str, object]]:
    """Return top-N chunks matching a text query using PostgreSQL FTS."""

    if limit <= 0:
        return []

    query = text(
        """
        SELECT
            c.id,
            c.repository_id,
            c.file_path,
            c.line_start,
            c.line_end,
            c.content,
            ts_rank_cd(
                to_tsvector('english', c.content),
                websearch_to_tsquery(:query_text)
            ) AS score
        FROM chunks AS c
        WHERE c.repository_id = :repository_id
          AND to_tsvector('english', c.content) @@ websearch_to_tsquery(:query_text)
        ORDER BY score DESC
        LIMIT :limit
        """
    )

    rows = (
        await session.execute(
            query,
            {
                "query_text": query_text,
                "repository_id": repository_id,
                "limit": limit,
            },
        )
    ).mappings().all()

    return [
        {
            "id": row["id"],
            "repository_id": row["repository_id"],
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "score": float(row["score"]),
        }
        for row in rows
    ]
