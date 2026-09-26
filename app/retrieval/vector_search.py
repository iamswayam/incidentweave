"""Vector similarity search over repository chunks."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Chunk


async def search_vector(
    session: AsyncSession,
    repository_id: int,
    query_embedding: list[float],
    limit: int = 10,
) -> list[dict[str, object]]:
    """Return the top-N chunks by pgvector cosine distance for a repository."""

    if limit <= 0:
        return []

    distance = Chunk.embedding.cosine_distance(query_embedding).label("distance")
    query = (
        select(
            Chunk.id,
            Chunk.repository_id,
            Chunk.file_path,
            Chunk.line_start,
            Chunk.line_end,
            Chunk.content,
            distance,
        )
        .where(
            Chunk.repository_id == repository_id,
            Chunk.embedding.is_not(None),
        )
        .order_by(distance)
        .limit(limit)
    )

    rows = (
        await session.execute(query)
    ).mappings().all()

    return [
        {
            "id": row["id"],
            "repository_id": row["repository_id"],
            "file_path": row["file_path"],
            "line_start": row["line_start"],
            "line_end": row["line_end"],
            "content": row["content"],
            "distance": float(row["distance"]),
        }
        for row in rows
    ]
