"""PostgreSQL integration tests for the Phase 2 database foundation."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal

pytestmark = pytest.mark.integration


def _database_url() -> str:
    return os.environ.get(
        "DATABASE_URL",
        "postgresql+psycopg://incidentweave:incidentweave@localhost:5432/incidentweave",
    ).replace("postgresql://", "postgresql+psycopg://", 1)


@pytest.mark.anyio
async def test_pgvector_extension_and_vector_column() -> None:
    """Verify pgvector is enabled and the chunk embedding is VECTOR(768)."""

    engine = create_async_engine(_database_url())

    async with engine.connect() as connection:
        extension_result = await connection.execute(
            text(
                "SELECT 1 FROM pg_extension "
                "WHERE extname = 'vector'"
            )
        )
        assert extension_result.scalar_one_or_none() == 1

        column_result = await connection.execute(
            text(
                "SELECT format_type(a.atttypid, a.atttypmod) "
                "FROM pg_attribute a "
                "JOIN pg_class c ON c.oid = a.attrelid "
                "WHERE c.relname = 'chunks' AND a.attname = 'embedding'"
            )
        )
        assert column_result.scalar_one() == "vector(768)"

    await engine.dispose()


@pytest.mark.anyio
async def test_repository_and_chunk_persistence() -> None:
    """Verify SQLAlchemy can persist and read a repository and chunk."""

    async with AsyncSessionLocal() as session:
        repository = Repository(name="phase2-test-repository")
        session.add(repository)
        await session.flush()

        chunk = Chunk(
            repository_id=repository.id,
            content="Phase 2 persistence test",
            file_path="tests/example.py",
            file_type="python",
            line_start=1,
            line_end=1,
            embedding=[0.0] * 768,
        )
        session.add(chunk)
        await session.commit()

        await session.refresh(chunk)

        assert chunk.id is not None
        assert chunk.repository_id == repository.id

        await session.delete(repository)
        await session.commit()
