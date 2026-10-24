"""Build the offline retrieval fixture from cached embeddings and the evaluation DB."""

from __future__ import annotations

import asyncio
import gzip
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import select

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal
from evaluation.chunk_experiments import DEFAULT_STRATEGY, get_strategy
from evaluation.golden import load_golden_set
from scripts.embed_chunks import GEMINI_MODEL
from scripts.ingest_repo import CHUNKER_VERSION

ROOT = Path(__file__).resolve().parents[1]
GOLDEN_PATH = ROOT / "evaluation" / "golden_set.json"
CACHE_ROOT = ROOT / "evaluation" / "cache"
FIXTURE_PATH = ROOT / "evaluation" / "fixtures" / "retrieval_fixture.json.gz"
MAX_FIXTURE_BYTES = int(1.5 * 1024 * 1024)
EVALUATION_REPOSITORY = get_strategy(DEFAULT_STRATEGY).evaluation_repository


def serialize_fixture(fixture: dict[str, Any]) -> bytes:
    """Serialize a fixture as compact, deterministic gzip-compressed JSON."""

    payload = json.dumps(
        fixture,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return gzip.compress(payload, mtime=0)


def write_fixture(fixture: dict[str, Any], path: Path) -> int:
    """Write a compressed fixture only if it is below the committed-size limit."""

    compressed = serialize_fixture(fixture)
    if len(compressed) >= MAX_FIXTURE_BYTES:
        raise ValueError(
            f"retrieval fixture is {len(compressed)} bytes; "
            f"must be under {MAX_FIXTURE_BYTES} bytes"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(compressed)
    return len(compressed)


def load_fixture(path: Path) -> dict[str, Any]:
    """Load a compressed JSON retrieval fixture."""

    return json.loads(gzip.decompress(path.read_bytes()))


def _round_embedding(embedding: list[float]) -> list[float]:
    return [round(float(value), 6) for value in embedding]


async def build_fixture(path: Path = FIXTURE_PATH) -> int:
    """Read existing evaluation chunks and cached question vectors, then write fixture."""

    golden = load_golden_set(GOLDEN_PATH)
    strategy = get_strategy(DEFAULT_STRATEGY)
    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == strategy.evaluation_repository)
        )
        if repository is None:
            raise RuntimeError(
                f"Evaluation repository {strategy.evaluation_repository!r} was not found"
            )
        rows = (
            await session.execute(
                select(
                    Chunk.file_path,
                    Chunk.line_start,
                    Chunk.line_end,
                    Chunk.content,
                    Chunk.embedding,
                )
                .where(Chunk.repository_id == repository.id)
                .order_by(Chunk.file_path, Chunk.line_start, Chunk.id)
            )
        ).all()

    missing_chunks = [
        f"{file_path}:{line_start}-{line_end}"
        for file_path, line_start, line_end, _content, embedding in rows
        if embedding is None
    ]
    if missing_chunks:
        raise RuntimeError("Chunks missing embeddings: " + ", ".join(missing_chunks))

    queries: dict[str, list[float]] = {}
    missing_queries: list[str] = []
    for question in golden["questions"]:
        key = hashlib.sha256(question["question"].encode("utf-8")).hexdigest()
        cache_path = CACHE_ROOT / f"{key}.json"
        if not cache_path.is_file():
            missing_queries.append(str(question["id"]))
            continue
        queries[str(question["id"])] = _round_embedding(
            json.loads(cache_path.read_text(encoding="utf-8"))
        )
    if missing_queries:
        raise RuntimeError(
            "Questions missing cached embeddings: " + ", ".join(missing_queries)
        )

    fixture = {
        "meta": {
            "pinned_sha": golden["pinned_sha"],
            "chunker_version": CHUNKER_VERSION,
            "strategy": strategy.name,
            "embedding_model": GEMINI_MODEL,
            "built_at": datetime.now(UTC).isoformat(),
            "chunk_count": len(rows),
            "question_count": len(queries),
        },
        "chunks": [
            {
                "file_path": file_path,
                "line_start": line_start,
                "line_end": line_end,
                "content": content,
                "embedding": _round_embedding(embedding),
            }
            for file_path, line_start, line_end, content, embedding in rows
        ],
        "queries": queries,
    }
    size = write_fixture(fixture, path)
    print(f"Fixture size: {size} bytes")
    return size


def main() -> None:
    try:
        asyncio.run(build_fixture())
    except (OSError, RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc


if __name__ == "__main__":
    main()
