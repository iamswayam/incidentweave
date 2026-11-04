"""CLI for ingesting a local repository into IncidentWeave."""

from __future__ import annotations

import argparse
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.ingestion import ingest_repository  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest a local Python repository into the IncidentWeave chunk table."
    )
    parser.add_argument("repo_path", help="Path to the local repository to ingest")
    parser.add_argument("repo_name", help="Repository name to store in the database")
    args = parser.parse_args()

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
