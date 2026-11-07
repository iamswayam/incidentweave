"""Read and summarize provider usage recorded in the application database."""

from __future__ import annotations

import argparse
import asyncio
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db.models import Audit, Investigation, ProviderUsageLog
from app.db.session import AsyncSessionLocal
from app.providers.operational_metrics import (
    summarize_operational_metrics,
)
from app.providers.operational_report import (
    format_operational_markdown,
    format_operational_text,
)
from app.providers.usage_report import (
    EMPTY_REPORT,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since-hours", type=int, default=24)
    parser.add_argument(
        "--format",
        choices=("text", "markdown"),
        default="text",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="write the Markdown report to this path",
    )
    return parser


def _usage_statement(cutoff: datetime, *, include_correlation_id: bool = False):
    columns = [
        ProviderUsageLog.provider,
        ProviderUsageLog.model,
        ProviderUsageLog.operation_tag,
        ProviderUsageLog.status,
        ProviderUsageLog.error_class,
        ProviderUsageLog.attempt_count,
        ProviderUsageLog.latency_ms,
        ProviderUsageLog.input_tokens,
        ProviderUsageLog.output_tokens,
    ]
    if include_correlation_id:
        columns.append(ProviderUsageLog.correlation_id)
    return (
        select(*columns)
        .where(ProviderUsageLog.created_at >= cutoff)
        .order_by(ProviderUsageLog.created_at, ProviderUsageLog.id)
    )


async def _load_rows(since_hours: int) -> list[dict[str, Any]]:
    """Load provider usage rows while preserving the original report query shape."""

    cutoff = datetime.now(UTC) - timedelta(hours=since_hours)
    async with AsyncSessionLocal() as session:
        result = await session.execute(_usage_statement(cutoff))
        return [dict(row._mapping) for row in result]


async def _load_operational_rows(
    since_hours: int,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Load usage and investigation/audit telemetry for one shared time window.

    The aggregation deduplicates investigations and uses the latest Audit.id trace.
    """

    cutoff = datetime.now(UTC) - timedelta(hours=since_hours)
    investigation_statement = (
        select(
            Investigation.id.label("investigation_id"),
            Investigation.outcome,
            Audit.id.label("audit_id"),
            Audit.trace,
        )
        .outerjoin(Audit, Audit.investigation_id == Investigation.id)
        .where(Investigation.created_at >= cutoff)
        .order_by(Investigation.created_at, Investigation.id, Audit.id)
    )
    async with AsyncSessionLocal() as session:
        usage_result = await session.execute(_usage_statement(cutoff, include_correlation_id=True))
        investigation_result = await session.execute(investigation_statement)
        usage_rows = [dict(row._mapping) for row in usage_result]
        investigation_rows = [dict(row._mapping) for row in investigation_result]
    return usage_rows, investigation_rows


async def _run(args: argparse.Namespace) -> int:
    if args.since_hours < 0:
        raise ValueError("--since-hours must be non-negative")
    usage_rows, investigation_rows = await _load_operational_rows(args.since_hours)
    summary = summarize_operational_metrics(
        usage_rows,
        investigation_rows,
        since_hours=args.since_hours,
    )
    markdown = format_operational_markdown(summary)
    if args.output is not None:
        args.output.write_text(markdown + "\n", encoding="utf-8")
        return 0
    if not usage_rows and not investigation_rows:
        print(EMPTY_REPORT)
        return 0
    formatter = (
        format_operational_markdown if args.format == "markdown" else format_operational_text
    )
    print(formatter(summary))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    return asyncio.run(_run(args))


if __name__ == "__main__":
    raise SystemExit(main())
