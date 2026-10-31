"""PostgreSQL integration tests for the degraded lexical-only retrieval path."""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.degraded_search import search_degraded_lexical_only

pytestmark = pytest.mark.integration


@pytest.mark.anyio
async def test_degraded_lexical_search_orders_ties_by_location_not_chunk_id() -> None:
    repository_name = f"degraded-search-test-{uuid4().hex}"
    content = "commonterm identical text"
    optional_content = "optionalword identical text"
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    inserted_locations = [
        ("src/z.py", 20, 24),
        ("src/a.py", 10, 14),
        ("src/a.py", 2, 6),
    ]

    try:
        async with AsyncSessionLocal() as session:
            repository = Repository(name=repository_name)
            session.add(repository)
            await session.flush()
            repository_id = repository.id
            session.add_all(
                [
                    Chunk(
                        repository_id=repository_id,
                        content=content,
                        content_hash=content_hash,
                        file_path=file_path,
                        line_start=line_start,
                        line_end=line_end,
                        embedding=None,
                    )
                    for file_path, line_start, line_end in inserted_locations
                ]
            )
            session.add(
                Chunk(
                    repository_id=repository_id,
                    content=optional_content,
                    content_hash=hashlib.sha256(
                        optional_content.encode("utf-8")
                    ).hexdigest(),
                    file_path="src/m.py",
                    line_start=15,
                    line_end=19,
                    embedding=None,
                )
            )
            await session.commit()

        async with AsyncSessionLocal() as session:
            results = await search_degraded_lexical_only(
                session,
                repository_id,
                "commonterm optionalword",
                limit=4,
            )

        assert [
            (item["file_path"], item["line_start"], item["line_end"])
            for item in results
        ] == [
            ("src/a.py", 2, 6),
            ("src/a.py", 10, 14),
            ("src/m.py", 15, 19),
            ("src/z.py", 20, 24),
        ]
        assert all(item["rrf_score"] is None for item in results)
        assert all(item["vector_score"] is None for item in results)
    finally:
        async with AsyncSessionLocal() as session:
            repository = await session.scalar(
                select(Repository).where(Repository.name == repository_name)
            )
            if repository is not None:
                await session.delete(repository)
            await session.commit()
