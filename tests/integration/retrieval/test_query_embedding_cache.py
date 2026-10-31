from __future__ import annotations

import importlib.util
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import AsyncIterator
from uuid import uuid4

import pytest
from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import inspect, select, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import settings
from app.db.models import QueryEmbeddingCache
from app.retrieval.query_embedding_cache import (
    CACHE_MAX_ROWS,
    build_query_embedding_key,
    get_query_embedding,
    put_query_embedding,
)

pytestmark = pytest.mark.integration


def _async_database_url() -> str:
    url = settings.database_url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+psycopg://", 1)
    return url


@asynccontextmanager
async def _isolated_schema() -> AsyncIterator[AsyncConnection]:
    engine = create_async_engine(_async_database_url())
    connection = await engine.connect()
    transaction = await connection.begin()
    schema = f"query_cache_test_{uuid4().hex}"
    try:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.execute(text(f'SET LOCAL search_path TO "{schema}"'))
        yield connection
    finally:
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


def _session_factory(connection: AsyncConnection):
    return async_sessionmaker(
        bind=connection,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest.mark.anyio
async def test_query_embedding_cache_hit_miss_and_key_variation() -> None:
    async with _isolated_schema() as connection:
        await connection.run_sync(QueryEmbeddingCache.__table__.create)
        async with _session_factory(connection)() as session:
            key = build_query_embedding_key("test-model", "default", 3, "question")
            assert await get_query_embedding(session, key) is None

            await put_query_embedding(session, key, [0.1, 0.2, 0.3])
            assert await get_query_embedding(session, key) == [0.1, 0.2, 0.3]
            assert (
                await get_query_embedding(
                    session,
                    build_query_embedding_key(
                        "test-model", "CODE_RETRIEVAL_QUERY", 3, "question"
                    ),
                )
                is None
            )


@pytest.mark.anyio
async def test_query_embedding_cache_expires_rows_after_ttl() -> None:
    async with _isolated_schema() as connection:
        await connection.run_sync(QueryEmbeddingCache.__table__.create)
        async with _session_factory(connection)() as session:
            key = build_query_embedding_key("test-model", "default", 2, "expired")
            session.add(
                QueryEmbeddingCache(
                    embedding_model=key.embedding_model,
                    task_type=key.task_type,
                    dimensions=key.dimensions,
                    query_hash=key.query_hash,
                    vector=[0.1, 0.2],
                    created_at=datetime.now(UTC) - timedelta(days=31),
                )
            )
            await session.flush()

            assert await get_query_embedding(session, key) is None
            assert (
                await session.scalar(
                    select(QueryEmbeddingCache.id).where(
                        QueryEmbeddingCache.query_hash == key.query_hash
                    )
                )
                is None
            )


@pytest.mark.anyio
async def test_query_embedding_cache_ignores_invalid_vector_dimensions() -> None:
    async with _isolated_schema() as connection:
        await connection.run_sync(QueryEmbeddingCache.__table__.create)
        async with _session_factory(connection)() as session:
            key = build_query_embedding_key("test-model", "default", 3, "invalid")
            session.add(
                QueryEmbeddingCache(
                    embedding_model=key.embedding_model,
                    task_type=key.task_type,
                    dimensions=key.dimensions,
                    query_hash=key.query_hash,
                    vector=[0.1, 0.2],
                )
            )
            await session.flush()

            assert await get_query_embedding(session, key) is None
            await session.commit()
            assert (
                await session.scalar(
                    select(QueryEmbeddingCache.id).where(
                        QueryEmbeddingCache.query_hash == key.query_hash
                    )
                )
                is None
            )


@pytest.mark.anyio
async def test_query_embedding_cache_enforces_cap_with_oldest_first_eviction() -> None:
    async with _isolated_schema() as connection:
        await connection.run_sync(QueryEmbeddingCache.__table__.create)
        async with _session_factory(connection)() as session:
            created_at = datetime.now(UTC) - timedelta(days=1)
            session.add_all(
                [
                    QueryEmbeddingCache(
                        embedding_model="cap-test",
                        task_type="default",
                        dimensions=1,
                        query_hash=f"{index:064x}",
                        vector=[0.5],
                        created_at=created_at + timedelta(microseconds=index),
                    )
                    for index in range(CACHE_MAX_ROWS + 1)
                ]
            )
            await session.flush()

            newest_key = build_query_embedding_key(
                "cap-test", "default", 1, "new entry"
            )
            await put_query_embedding(session, newest_key, [0.9])

            count = await session.scalar(
                select(text("count(*)")).select_from(QueryEmbeddingCache)
            )
            oldest_hashes = (
                await session.execute(
                    select(QueryEmbeddingCache.query_hash)
                    .where(QueryEmbeddingCache.embedding_model == "cap-test")
                    .order_by(QueryEmbeddingCache.created_at, QueryEmbeddingCache.id)
                    .limit(2)
                )
            ).scalars().all()
            stored_hashes = set(
                (
                    await session.execute(
                        select(QueryEmbeddingCache.query_hash).where(
                            QueryEmbeddingCache.embedding_model == "cap-test"
                        )
                    )
                )
                .scalars()
                .all()
            )

            assert count == CACHE_MAX_ROWS
            assert (
                "0000000000000000000000000000000000000000000000000000000000000000"
                not in stored_hashes
            )
            assert (
                "0000000000000000000000000000000000000000000000000000000000000001"
                not in stored_hashes
            )
            assert newest_key.query_hash in stored_hashes
            assert len(oldest_hashes) == 2


@pytest.mark.anyio
async def test_query_embedding_cache_migration_upgrades_and_downgrades() -> None:
    migration_path = (
        Path(__file__).resolve().parents[3]
        / "migrations"
        / "versions"
        / "20261031_0006_query_embedding_cache.py"
    )
    spec = importlib.util.spec_from_file_location("query_embedding_cache_migration", migration_path)
    assert spec is not None and spec.loader is not None
    migration = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(migration)

    async with _isolated_schema() as connection:
        schema_name = str(
            (await connection.execute(text("SELECT current_schema()"))).scalar_one()
        )

        def verify_upgrade(sync_connection) -> None:
            migration_context = MigrationContext.configure(sync_connection)
            with Operations.context(migration_context):
                migration.upgrade()
            inspector = inspect(sync_connection)
            assert "query_embedding_cache" in inspector.get_table_names(
                schema=schema_name
            )
            indexes = inspector.get_indexes(
                "query_embedding_cache",
                schema=schema_name,
            )
            assert any(
                index["name"] == "uq_query_embedding_cache_identity"
                and index["unique"]
                for index in indexes
            )

        await connection.run_sync(verify_upgrade)

        def verify_downgrade(sync_connection) -> None:
            migration_context = MigrationContext.configure(sync_connection)
            with Operations.context(migration_context):
                migration.downgrade()
            assert "query_embedding_cache" not in inspect(
                sync_connection
            ).get_table_names(schema=schema_name)

        await connection.run_sync(verify_downgrade)
