"""Ingest a local repository into the IncidentWeave chunk schema."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, Repository
from app.db.session import AsyncSessionLocal

CHUNK_SIZE = 60
OVERLAP_SIZE = 10
IGNORE_DIRS = {".venv", "__pycache__", ".git", "migrations"}


def iter_python_files(repo_root: Path):
    """Yield Python files under the repo root while skipping excluded directories."""

    for file_path in repo_root.rglob("*.py"):
        if not file_path.is_file():
            continue

        relative_parts = file_path.relative_to(repo_root).parts
        if any(part in IGNORE_DIRS for part in relative_parts):
            continue

        yield file_path


def chunk_lines(lines: list[str], chunk_size: int = CHUNK_SIZE, overlap: int = OVERLAP_SIZE):
    """Yield fixed-size windows with a small overlap between consecutive chunks."""

    if not lines:
        return

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap_size")

    for start_index in range(0, len(lines), step):
        end_index = min(start_index + chunk_size, len(lines))
        yield start_index, end_index


async def ingest_repository(repo_path: str, repo_name: str) -> tuple[int, int]:
    """Ingest all Python files under a local repository into the chunk table."""

    root = Path(repo_path).resolve()
    if not root.exists() or not root.is_dir():
        raise FileNotFoundError(f"Repository path not found or not a directory: {repo_path}")

    async with AsyncSessionLocal() as session:
        repository = await session.scalar(
            select(Repository).where(Repository.name == repo_name)
        )

        if repository is None:
            repository = Repository(name=repo_name)
            session.add(repository)
            await session.flush()

        files_processed = 0
        chunks_to_create: list[Chunk] = []

        for file_path in sorted(iter_python_files(root)):
            files_processed += 1
            relative_path = file_path.relative_to(root).as_posix()

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            for start_index, end_index in chunk_lines(lines):
                chunk_lines = lines[start_index:end_index]
                chunk_content = "\n".join(chunk_lines)

                if not chunk_content.strip():
                    continue

                chunks_to_create.append(
                    Chunk(
                        repository_id=repository.id,
                        content=chunk_content,
                        file_path=relative_path,
                        file_type="python",
                        document_type="code",
                        line_start=start_index + 1,
                        line_end=end_index,
                        function_name=None,
                        class_name=None,
                        symbol=None,
                    )
                )

        session.add_all(chunks_to_create)
        await session.commit()

        return files_processed, len(chunks_to_create)


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""

    parser = argparse.ArgumentParser(
        description="Ingest a local Python repository into the IncidentWeave chunk table."
    )
    parser.add_argument("repo_path", help="Path to the local repository to ingest")
    parser.add_argument("repo_name", help="Repository name to store in the database")
    return parser.parse_args()


def main() -> None:
    """Run the repository ingestion CLI."""

    args = parse_args()

    try:
        files_processed, chunks_created = __import__("asyncio").run(
            ingest_repository(args.repo_path, args.repo_name)
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Files processed: {files_processed}")
    print(f"Chunks created: {chunks_created}")


if __name__ == "__main__":
    main()
