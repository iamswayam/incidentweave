"""PostgreSQL integration tests for deterministic retrieval tie ordering."""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.hybrid_search import hybrid_search
from app.retrieval.vector_search import search_vector

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_search_orders_ties_identically_across_chunk_id_offsets() -> None:
    session_factory = AsyncSessionLocal
    repository_names = [f"ordering-test-{uuid4().hex}" for _ in range(2)]
    expected = [
        ("src/a.py", 2, 6),
        ("src/a.py", 10, 14),
        ("src/z.py", 20, 24),
    ]
    embedding = [1.0] + [0.0] * 767
    content = "commonterm identical text"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    chunks = [
        ("src/z.py", 20, 24),
        ("src/a.py", 10, 14),
        ("src/a.py", 2, 6),
    ]

    try:
        async with session_factory() as session:
            repository_ids = []
            for name in repository_names:
                repository = Repository(name=name)
                session.add(repository)
                await session.flush()
                repository_ids.append(repository.id)
                session.add_all(
                    [
                        Chunk(
                            repository_id=repository.id,
                            content=content,
                            content_hash=content_hash,
                            file_path=file_path,
                            line_start=line_start,
                            line_end=line_end,
                            embedding=embedding,
                        )
                        for file_path, line_start, line_end in chunks
                    ]
                )
            await session.commit()

        orders = []
        async with session_factory() as session:
            for repository_id in repository_ids:
                vector_results = await search_vector(
                    session,
                    repository_id,
                    embedding,
                    limit=len(chunks),
                )
                fts_results = await search_fulltext(
                    session,
                    repository_id,
                    "commonterm",
                    limit=len(chunks),
                )
                hybrid_results = await hybrid_search(
                    session,
                    repository_id,
                    "commonterm",
                    embedding,
                    limit=len(chunks),
                )
                orders.append(
                    [
                        [
                            (result["file_path"], result["line_start"], result["line_end"])
                            for result in results
                        ]
                        for results in (vector_results, fts_results, hybrid_results)
                    ]
                )

        assert orders[0] == orders[1]
        assert orders[0] == [expected, expected, expected]
    finally:
        async with session_factory() as session:
            for name in repository_names:
                repository = await session.scalar(
                    select(Repository).where(Repository.name == name)
                )
                if repository is not None:
                    await session.delete(repository)
            await session.commit()
