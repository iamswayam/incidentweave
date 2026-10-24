"""Ingest a local repository into the IncidentWeave chunk schema."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from sqlalchemy import delete, select

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.db.models import Chunk, IngestRun, Repository  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.secret_scan import find_secret  # noqa: E402

CHUNK_SIZE = 60
OVERLAP_SIZE = 10
CHUNKER_VERSION = "lines-60-10-v1"
IGNORE_DIRS = {
    ".git",
    ".kilo",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "migrations",
}


def _run_git(root: Path, *arguments: str) -> str | None:
    try:
        completed = subprocess.run(
            ["git", *arguments],
            cwd=root,
            capture_output=True,
            text=True,
            check=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return completed.stdout.strip()


def _strip_remote_credentials(remote_url: str) -> str:
    parts = urlsplit(remote_url)
    if parts.scheme and parts.netloc and "@" in parts.netloc:
        return urlunsplit(parts._replace(netloc=parts.netloc.rsplit("@", 1)[-1]))
    return remote_url


def _git_metadata(root: Path) -> tuple[str | None, bool | None, str | None]:
    commit_sha = _run_git(root, "rev-parse", "HEAD") or None
    status = _run_git(root, "status", "--porcelain")
    dirty = None if status is None else bool(status)
    remote = _run_git(root, "config", "--get", "remote.origin.url") or None
    if remote is not None:
        remote = _strip_remote_credentials(remote)
    return commit_sha, dirty, remote


def _chunk_identity(chunk: Chunk) -> tuple[str, int | None, int | None, str]:
    return (chunk.file_path, chunk.line_start, chunk.line_end, chunk.content_hash)


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
    """Yield windows only when they add at least one new line beyond the prior window."""

    if not lines:
        return

    step = chunk_size - overlap
    if step <= 0:
        raise ValueError("chunk_size must be greater than overlap_size")

    previous_end = 0
    for start_index in range(0, len(lines), step):
        end_index = min(start_index + chunk_size, len(lines))

        if end_index <= previous_end:
            continue

        yield start_index, end_index
        previous_end = end_index


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

        commit_sha, dirty, git_remote = _git_metadata(root)
        ingest_run = IngestRun(
            repository_id=repository.id,
            source_path=str(root),
            git_remote=git_remote,
            commit_sha=commit_sha,
            dirty=dirty,
            chunker_version=CHUNKER_VERSION,
        )
        session.add(ingest_run)
        await session.flush()

        existing_chunks = list(
            (
                await session.scalars(
                    select(Chunk).where(Chunk.repository_id == repository.id)
                )
            ).all()
        )
        existing_by_identity = {
            _chunk_identity(chunk): chunk for chunk in existing_chunks
        }

        files_processed = 0
        chunks_to_create: list[Chunk] = []
        skipped_chunks: list[tuple[str, str, int, int]] = []
        current_identities: set[tuple[str, int | None, int | None, str]] = set()
        kept_chunks = 0

        for file_path in sorted(iter_python_files(root)):
            files_processed += 1
            relative_path = file_path.relative_to(root).as_posix()

            content = file_path.read_text(encoding="utf-8", errors="replace")
            lines = content.splitlines()

            for start_index, end_index in chunk_lines(lines):
                window_lines = lines[start_index:end_index]
                chunk_content = "\n".join(window_lines)

                if not chunk_content.strip():
                    continue

                line_start = start_index + 1
                line_end = end_index
                secret_pattern = find_secret(chunk_content)
                if secret_pattern is not None:
                    skipped_chunks.append(
                        (secret_pattern, relative_path, line_start, line_end)
                    )
                    continue

                content_hash = hashlib.sha256(
                    chunk_content.encode("utf-8")
                ).hexdigest()
                identity = (relative_path, line_start, line_end, content_hash)
                current_identities.add(identity)
                if identity in existing_by_identity:
                    kept_chunks += 1
                    continue

                chunks_to_create.append(
                    Chunk(
                        repository_id=repository.id,
                        ingest_run_id=ingest_run.id,
                        content=chunk_content,
                        content_hash=content_hash,
                        file_path=relative_path,
                        file_type="python",
                        document_type="code",
                        line_start=line_start,
                        line_end=line_end,
                        function_name=None,
                        class_name=None,
                        symbol=None,
                    )
                )

        removed_chunk_ids = [
            chunk.id
            for identity, chunk in existing_by_identity.items()
            if identity not in current_identities
        ]
        if removed_chunk_ids:
            await session.execute(delete(Chunk).where(Chunk.id.in_(removed_chunk_ids)))

        session.add_all(chunks_to_create)
        await session.commit()

        for pattern_name, relative_path, line_start, line_end in skipped_chunks:
            print(
                "Skipped chunk with possible secret "
                f"({pattern_name}): {relative_path}:{line_start}-{line_end}"
            )

        added_chunks = len(chunks_to_create)
        print(
            "Chunks kept/added/removed: "
            f"{kept_chunks}/{added_chunks}/{len(removed_chunk_ids)}"
        )
        return files_processed, kept_chunks + added_chunks


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
        files_processed, total_chunks = asyncio.run(
            ingest_repository(args.repo_path, args.repo_name)
        )
    except FileNotFoundError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(2)

    print(f"Files processed: {files_processed}")
    print(f"Chunks present: {total_chunks}")


if __name__ == "__main__":
    main()
