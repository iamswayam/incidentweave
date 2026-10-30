"""Read and summarize provider usage recorded in the application database."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select

from app.db.models import ProviderUsageLog
from app.db.session import AsyncSessionLocal
from app.providers.usage_report import (
    EMPTY_REPORT,
    format_markdown,
    format_text,
    summarize,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-hours", type=int, default=24)
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
    )
    return parser


async def _load_rows(since_hours: int) -> list[dict[str, Any]]:
    cutoff = datetime.now(UTC) - timedelta(hours=since_hours)
    statement = (
        select(
            ProviderUsageLog.provider,
            ProviderUsageLog.model,
            ProviderUsageLog.operation_tag,
            ProviderUsageLog.status,
            ProviderUsageLog.error_class,
            ProviderUsageLog.attempt_count,
            ProviderUsageLog.latency_ms,
            ProviderUsageLog.input_tokens,
            ProviderUsageLog.output_tokens,
        )
        .where(ProviderUsageLog.created_at >= cutoff)
        .order_by(ProviderUsageLog.created_at, ProviderUsageLog.id)
    )
    async with AsyncSessionLocal() as session:
        result = await session.execute(statement)
        return [dict(row._mapping) for row in result]


async def _run(args: argparse.Namespace) -> int:
    if args.since_hours < 0:
        raise ValueError("--since-hours must be non-negative")
    rows = await _load_rows(args.since_hours)
    if not rows:
        print(EMPTY_REPORT)
        return 0
    summary = summarize(rows)
    formatter = format_markdown if args.format == "markdown" else format_text
    print(formatter(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
