"""CLI for embedding repository chunks with Gemini."""

from __future__ import annotations

import argparse
import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.retrieval.embeddings import embed_repository_chunks  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Embed all unembedded repository chunks with Gemini gemini-embedding-001."
    )
    parser.add_argument("repo_name", help="Repository name as stored in the database")
    args = parser.parse_args()

    try:
        embedded, failed, skipped = asyncio.run(embed_repository_chunks(args.repo_name))
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
