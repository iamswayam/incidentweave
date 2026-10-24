"""Live Gemini benchmark: sends existing database chunk text to the embedding API.

This script makes live Gemini calls and only reads from the database; it does not
write embeddings or modify database rows.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.providers import gemini  # noqa: E402
from scripts.embed_chunks import (  # noqa: E402
    EMBED_BATCH_SIZE,
    EMBED_CONCURRENCY,
    embed_text,
    embed_texts,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Benchmark live Gemini single and batch embedding requests."
    )
    parser.add_argument("repo_name", help="Repository name stored in the database")
    parser.add_argument("--count", type=int, default=100, help="Batch benchmark chunk count")
    parser.add_argument(
        "--single-sample",
        type=int,
        default=20,
        help="Number of sequential single-text embedding calls",
    )
    return parser.parse_args()


async def benchmark(repo_name: str, count: int, single_sample: int) -> None:
    if count < 1 or single_sample < 1:
        raise ValueError("--count and --single-sample must be greater than zero")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")
        query_count = max(count, single_sample)
        rows = (
            await session.scalars(
                select(Chunk.content)
                .where(Chunk.repository_id == repository.id)
                .order_by(Chunk.id)
                .limit(query_count)
            )
        ).all()
    if len(rows) < query_count:
        raise ValueError(f"Repository has only {len(rows)} chunks; {query_count} requested")

    original_send_once = gemini.send_once
    attempt_count = 0
    logical_requests = single_sample + (count + EMBED_BATCH_SIZE - 1) // EMBED_BATCH_SIZE

    async def counted_send_once(client, url, payload):
        nonlocal attempt_count
        attempt_count += 1
        return await original_send_once(client, url, payload)

    gemini.send_once = counted_send_once
    try:
        single_start = time.perf_counter()
        for text in rows[:single_sample]:
            await embed_text(text)
        single_seconds = time.perf_counter() - single_start

        batch_start = time.perf_counter()
        semaphore = asyncio.Semaphore(EMBED_CONCURRENCY)
        batches = [
            rows[index : index + EMBED_BATCH_SIZE]
            for index in range(0, count, EMBED_BATCH_SIZE)
        ]

        async def embed_batch(batch: list[str]) -> None:
            async with semaphore:
                await embed_texts(batch)

        await asyncio.gather(*(embed_batch(batch) for batch in batches))
        batch_seconds = time.perf_counter() - batch_start
    finally:
        gemini.send_once = original_send_once

    print(
        f"Single sequential ({single_sample} chunks): {single_seconds:.3f}s, "
        f"{single_sample / single_seconds:.2f} chunks/s"
    )
    print(
        f"Batch concurrent ({count} chunks): {batch_seconds:.3f}s, "
        f"{count / batch_seconds:.2f} chunks/s"
    )
    print(f"Retries: {attempt_count - logical_requests}")


def main() -> None:
    args = parse_args()
    try:
        asyncio.run(benchmark(args.repo_name, args.count, args.single_sample))
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
