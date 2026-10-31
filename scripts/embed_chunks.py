"""Embed all unembedded chunks for a repository using the Gemini embedding API."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Literal

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.providers.gemini import (  # noqa: E402
    ProviderSchemaInvalidError,
    guarded_post_json,
    make_client,
)

GEMINI_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768
EMBED_BATCH_SIZE = 50
EMBED_CONCURRENCY = 4
EmbeddingTaskType = Literal["RETRIEVAL_DOCUMENT", "CODE_RETRIEVAL_QUERY"]


def _validate_embedding_options(
    task_type: EmbeddingTaskType | None,
    max_attempts: int,
) -> None:
    if task_type not in {None, "RETRIEVAL_DOCUMENT", "CODE_RETRIEVAL_QUERY"}:
        raise ValueError(f"Unsupported Gemini embedding task type: {task_type}")
    if type(max_attempts) is not int or max_attempts < 1:
        raise ValueError("max_attempts must be positive")


def _single_embedding_url() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"{GEMINI_MODEL}:embedContent"
    )


def _batch_embedding_url() -> str:
    return (
        f"https://generativelanguage.googleapis.com/v1beta/"
        f"{GEMINI_MODEL}:batchEmbedContents"
    )


async def embed_text(
    text: str,
    *,
    task_type: EmbeddingTaskType | None = None,
    max_attempts: int = 3,
) -> list[float]:
    """Embed one value, optionally selecting a retrieval-specific task."""

    payload = {
        "model": GEMINI_MODEL,
        "content": {"parts": [{"text": text}]},
        "outputDimensionality": EMBEDDING_DIMENSION,
    }
    _validate_embedding_options(task_type, max_attempts)
    if task_type is not None:
        payload["taskType"] = task_type
    async with make_client() as client:
        payload_data = await guarded_post_json(
            client,
            _single_embedding_url(),
            payload,
            deadline_seconds=60,
            max_attempts=max_attempts,
            operation_tag="query_embedding",
        )

    embedding = payload_data.get("embedding")
    values = embedding.get("values") if isinstance(embedding, dict) else None
    if not isinstance(values, list):
        raise ProviderSchemaInvalidError("Unexpected Gemini embedding response format")
    if len(values) != EMBEDDING_DIMENSION:
        raise ProviderSchemaInvalidError(
            f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}, "
            f"got {len(values)}"
        )
    try:
        return [float(value) for value in values]
    except (OverflowError, TypeError, ValueError) as exc:
        raise ProviderSchemaInvalidError(
            "Gemini embedding response contained a non-numeric value"
        ) from exc


async def embed_texts(
    texts: list[str],
    *,
    task_type: EmbeddingTaskType | None = None,
    max_attempts: int = 3,
) -> list[list[float]]:
    """Embed a batch, optionally selecting a retrieval-specific task."""

    _validate_embedding_options(task_type, max_attempts)
    requests = []
    for text in texts:
        request = {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
        if task_type is not None:
            request["taskType"] = task_type
        requests.append(request)
    payload = {"requests": requests}
    async with make_client() as client:
        payload_data = await guarded_post_json(
            client,
            _batch_embedding_url(),
            payload,
            deadline_seconds=60,
            max_attempts=max_attempts,
            operation_tag="document_embedding",
        )

    embeddings = payload_data.get("embeddings")
    if not isinstance(embeddings, list) or len(embeddings) != len(texts):
        raise ValueError("Unexpected Gemini batch embedding response count")
    vectors: list[list[float]] = []
    for embedding in embeddings:
        values = embedding.get("values") if isinstance(embedding, dict) else None
        if not isinstance(values, list) or len(values) != EMBEDDING_DIMENSION:
            raise ValueError(
                f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}"
            )
        vectors.append([float(value) for value in values])
    return vectors


async def embed_repository_chunks(repo_name: str) -> tuple[int, int, int]:
    """Embed all unembedded chunks for the given repository name."""

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )
        if repository is None:
            raise ValueError(f"Repository not found: {repo_name}")

        all_chunks = (
            await session.execute(
                select(Chunk).where(Chunk.repository_id == repository.id)
            )
        ).scalars().all()

        chunks_to_embed = [chunk for chunk in all_chunks if chunk.embedding is None]
        skipped = len(all_chunks) - len(chunks_to_embed)
        embedded = 0
        failed = 0

        semaphore = asyncio.Semaphore(EMBED_CONCURRENCY)
        batches = [
            chunks_to_embed[index : index + EMBED_BATCH_SIZE]
            for index in range(0, len(chunks_to_embed), EMBED_BATCH_SIZE)
        ]

        async def embed_batch(
            batch: list[Chunk],
        ) -> tuple[list[list[float]] | None, Exception | None]:
            async with semaphore:
                try:
                    return await embed_texts([chunk.content for chunk in batch]), None
                except (RuntimeError, TimeoutError, ValueError) as exc:
                    return None, exc

        results = await asyncio.gather(
            *(embed_batch(batch) for batch in batches),
        )
        for batch, (vectors, error) in zip(batches, results):
            if error is not None:
                print(
                    f"Failed to embed batch ({len(batch)} chunks): "
                    f"{type(error).__name__}",
                    file=sys.stderr,
                )
                failed += len(batch)
                continue
            assert vectors is not None
            for chunk, embedding in zip(batch, vectors):
                chunk.embedding = embedding
                session.add(chunk)
                embedded += 1

        await session.commit()

        return embedded, failed, skipped


def parse_args() -> argparse.Namespace:
    """Parse the repository name argument."""

    parser = argparse.ArgumentParser(
        description="Embed all unembedded repository chunks with Gemini gemini-embedding-001."
    )
    parser.add_argument("repo_name", help="Repository name as stored in the database")
    return parser.parse_args()


def main() -> None:
    """Run the chunk embedding CLI."""

    args = parse_args()

    try:
        embedded, failed, skipped = asyncio.run(
            embed_repository_chunks(args.repo_name)
        )
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Chunks embedded: {embedded}")
    print(f"Chunks failed: {failed}")
    print(f"Chunks skipped: {skipped}")


if __name__ == "__main__":
    main()
