"""PostgreSQL integration tests for deterministic retrieval tie ordering."""

import hashlib
from uuid import uuid4

import pytest
from sqlalchemy import select, text

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from app.retrieval.fulltext_search import search_fulltext
from app.retrieval.fulltext_variants import SEARCHABLE_TEXT_VERSION
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
                            (
                                result["file_path"],
                                result["line_start"],
                                result["line_end"],
                            )
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


@pytest.mark.anyio
async def test_default_fulltext_path_is_raw_and_c2_splits_chunk_text_only() -> None:
    repository_name = f"fulltext-variant-test-{uuid4().hex}"
    raw_match_content = "local = True"
    split_match_content = "client = AsyncSessionLocal()"

    try:
        async with AsyncSessionLocal() as session:
            repository = Repository(name=repository_name)
            session.add(repository)
            await session.flush()
            repository_id = repository.id
            raw_match = Chunk(
                repository_id=repository_id,
                file_path="src/a.py",
                line_start=1,
                line_end=1,
                content=raw_match_content,
                content_hash=hashlib.sha256(
                    raw_match_content.encode("utf-8")
                ).hexdigest(),
                embedding=[1.0] + [0.0] * 767,
            )
            split_match = Chunk(
                repository_id=repository_id,
                file_path="src/local_helper.py",
                line_start=2,
                line_end=2,
                content=split_match_content,
                content_hash=hashlib.sha256(
                    split_match_content.encode("utf-8")
                ).hexdigest(),
                embedding=[0.0, 1.0] + [0.0] * 766,
            )
            path_only_chunk = Chunk(
                repository_id=repository_id,
                file_path="src/local_only.py",
                line_start=3,
                line_end=3,
                content="plain identifier",
                content_hash=hashlib.sha256(
                    b"plain identifier"
                ).hexdigest(),
                embedding=[0.0, 1.0] + [0.0] * 766,
            )
            session.add_all([raw_match, split_match, path_only_chunk])
            await session.flush()
            raw_match_id = raw_match.id
            split_match_id = split_match.id
            await session.commit()

        async with AsyncSessionLocal() as session:
            previous_default_query = text(
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
                  AND to_tsvector('english', c.content)
                      @@ websearch_to_tsquery(:query_text)
                ORDER BY score DESC, c.file_path, c.line_start, c.line_end
                LIMIT :limit
                """
            )
            previous_rows = (
                await session.execute(
                    previous_default_query,
                    {
                        "query_text": "local",
                        "repository_id": repository_id,
                        "limit": 5,
                    },
                )
            ).mappings().all()
            previous_output = [
                {
                    "id": row["id"],
                    "repository_id": row["repository_id"],
                    "file_path": row["file_path"],
                    "line_start": row["line_start"],
                    "line_end": row["line_end"],
                    "content": row["content"],
                    "score": float(row["score"]),
                }
                for row in previous_rows
            ]
            default_results = await search_fulltext(
                session,
                repository_id,
                "local",
                limit=5,
            )
            c2_results = await search_fulltext(
                session,
                repository_id,
                "local",
                limit=5,
                query_text_override='"local"',
                searchable_text_version=SEARCHABLE_TEXT_VERSION,
            )

        assert default_results == previous_output
        assert [row["id"] for row in default_results] == [raw_match_id]
        assert [row["id"] for row in c2_results] == [
            raw_match_id,
            split_match_id,
        ]
        assert [row["content"] for row in c2_results] == [
            raw_match_content,
            split_match_content,
        ]
    finally:
        async with AsyncSessionLocal() as session:
            repository = await session.scalar(
                select(Repository).where(Repository.name == repository_name)
            )
            if repository is not None:
                await session.delete(repository)
                await session.commit()
