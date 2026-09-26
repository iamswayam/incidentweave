"""Embed all unembedded chunks for a repository using the Gemini embedding API."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from pathlib import Path
from urllib import error, request

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402

GEMINI_MODEL = "models/gemini-embedding-001"
EMBEDDING_DIMENSION = 768


def get_gemini_api_key() -> str:
    """Read the Gemini API key from environment configuration."""

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")
    return api_key


def embed_text(text: str) -> list[float]:
    """Call the Gemini embeddings API for a single text value."""

    api_key = get_gemini_api_key()
    payload = json.dumps(
        {
            "model": GEMINI_MODEL,
            "content": {"parts": [{"text": text}]},
            "outputDimensionality": EMBEDDING_DIMENSION,
        }
    ).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/{GEMINI_MODEL}:embedContent?key={api_key}"
    req = request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=60) as response:
            payload_data = json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API request failed: {detail}") from exc

    values = payload_data.get("embedding", {}).get("values")
    if not isinstance(values, list):
        raise ValueError("Unexpected Gemini embedding response format")

    if len(values) != EMBEDDING_DIMENSION:
        raise ValueError(
            f"Unexpected embedding dimension: expected {EMBEDDING_DIMENSION}, got {len(values)}"
        )

    return [float(value) for value in values]


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

        for chunk in chunks_to_embed:
            try:
                chunk.embedding = embed_text(chunk.content)
                session.add(chunk)
                embedded += 1
            except Exception as exc:  # pragma: no cover - runtime network/API behavior
                print(
                    f"Failed to embed chunk {chunk.id} ({chunk.file_path}): {exc}",
                    file=sys.stderr,
                )
                failed += 1
            finally:
                await asyncio.sleep(1.5)

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
