"""Persistent, query-text-free cache for query embeddings."""

from __future__ import annotations

import hashlib
import math
import re
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from numbers import Real

from sqlalchemy import delete, func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import QueryEmbeddingCache

CACHE_TTL = timedelta(days=30)
CACHE_MAX_ROWS = 10_000
_WHITESPACE_PATTERN = re.compile(r"\s+")
_CACHE_WRITE_LOCK_KEY = 1_342_177_298
_CACHE_KEY_COLUMNS = (
    "embedding_model",
    "task_type",
    "dimensions",
    "query_hash",
)


@dataclass(frozen=True)
class QueryEmbeddingKey:
    embedding_model: str
    task_type: str
    dimensions: int
    query_hash: str


def normalize_query(query: str) -> str:
    """Trim and collapse whitespace while preserving query case."""

    return _WHITESPACE_PATTERN.sub(" ", query).strip()


def build_query_embedding_key(
    embedding_model: str,
    task_type: str,
    dimensions: int,
    query: str,
) -> QueryEmbeddingKey:
    normalized_query = normalize_query(query)
    return QueryEmbeddingKey(
        embedding_model=embedding_model,
        task_type=task_type,
        dimensions=dimensions,
        query_hash=hashlib.sha256(normalized_query.encode("utf-8")).hexdigest(),
    )


def validate_cached_vector(vector: object, dimensions: int) -> list[float] | None:
    """Decode a stored JSON vector only when shape and numeric values are valid."""

    if not isinstance(vector, list) or len(vector) != dimensions:
        return None
    if any(
        isinstance(value, bool)
        or not isinstance(value, Real)
        or not math.isfinite(float(value))
        for value in vector
    ):
        return None
    return [float(value) for value in vector]


async def _expire_rows(session: AsyncSession) -> None:
    cutoff = datetime.now(UTC) - CACHE_TTL
    await session.execute(
        delete(QueryEmbeddingCache).where(QueryEmbeddingCache.created_at < cutoff)
    )


async def get_query_embedding(
    session: AsyncSession,
    key: QueryEmbeddingKey,
) -> list[float] | None:
    """Expire stale rows and return a compatible cached vector, if present."""

    await _expire_rows(session)
    row = await session.scalar(
        select(QueryEmbeddingCache).where(
                QueryEmbeddingCache.embedding_model == key.embedding_model,
                QueryEmbeddingCache.task_type == key.task_type,
                QueryEmbeddingCache.dimensions == key.dimensions,
                QueryEmbeddingCache.query_hash == key.query_hash,
        )
    )
    if row is None:
        return None
    vector = validate_cached_vector(row.vector, key.dimensions)
    if vector is None:
        await session.delete(row)
    return vector


async def put_query_embedding(
    session: AsyncSession,
    key: QueryEmbeddingKey,
    vector: list[float],
) -> None:
    """Insert a vector if absent and evict oldest rows to enforce the global cap."""

    validated = validate_cached_vector(vector, key.dimensions)
    if validated is None:
        raise ValueError("Query embedding vector does not match cache dimensions")

    await session.execute(
        text("SELECT pg_advisory_xact_lock(:lock_key)"),
        {"lock_key": _CACHE_WRITE_LOCK_KEY},
    )
    await _expire_rows(session)
    await session.execute(
        insert(QueryEmbeddingCache)
        .values(
            embedding_model=key.embedding_model,
            task_type=key.task_type,
            dimensions=key.dimensions,
            query_hash=key.query_hash,
            vector=validated,
        )
        .on_conflict_do_nothing(index_elements=list(_CACHE_KEY_COLUMNS))
    )
    row_count = int(
        await session.scalar(select(func.count()).select_from(QueryEmbeddingCache))
    )
    excess = row_count - CACHE_MAX_ROWS
    if excess > 0:
        oldest_ids = (
            select(QueryEmbeddingCache.id)
            .order_by(QueryEmbeddingCache.created_at.asc(), QueryEmbeddingCache.id.asc())
            .limit(excess)
        )
        await session.execute(
            delete(QueryEmbeddingCache).where(QueryEmbeddingCache.id.in_(oldest_ids))
        )
