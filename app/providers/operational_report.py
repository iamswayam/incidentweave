"""Deterministic text and Markdown formatting for operational metrics."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from app.providers.usage_report import EMPTY_REPORT


def _number(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, Decimal):
        return f"{value.quantize(Decimal('0.00000001'), rounding=ROUND_HALF_UP):f}"
    return str(value)


def _percent(value: Decimal | None) -> str:
    return "-" if value is None else f"{(value * 100).quantize(Decimal('0.01'))}%"


def _price(value: Decimal | None) -> str:
    return "no official price" if value is None else f"USD {_number(value)}"


def _markdown_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    if not rows:
        return ["No rows."]
    return [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
        *("| " + " | ".join(row) + " |" for row in rows),
    ]


def _method_lines(summary: Mapping[str, Any]) -> list[str]:
    return [
        "Method and caveats:",
        f"- Time window: last {summary['since_hours']} hours.",
        f"- Provider usage rows: {summary['usage_row_count']}.",
        "- Latency percentiles use nearest rank: sorted value at rank ceil(p*n), one-based.",
        "- List-price cost is an estimate from logged token counts; it is not billing data.",
        f"- Rows with null token counts: {summary['missing_token_rows']} "
        "(excluded from cost where required).",
        "- Prices are in app/providers/pricing.py; unpriced models are reported as "
        "no official price.",
        "- Observed (free tier): USD 0.00; provider billing actuals are not ingested or verified.",
        "- Estimated list-price and observed free-tier cost are separate, not added together.",
    ]


def format_operational_markdown(summary: Mapping[str, Any]) -> str:
    """Format a deterministic Markdown operational report."""

    lines = ["# Provider operational metrics", ""]
    if summary["generated_at"] is not None:
        lines.extend([f"Generated at: {summary['generated_at']}", ""])
    lines.extend(
        [
            f"Time window: last {summary['since_hours']} hours.",
            f"Provider usage rows: {summary['usage_row_count']}.",
            "",
            "## Per-operation metrics",
            "",
        ]
    )
    operation_rows = [
        [
            row["operation"],
            _number(row["count"]),
            _number(row["errors"]),
            _percent(row["error_rate"]),
            _number(row["attempts"]),
            _number(row["p50_ms"]),
            _number(row["p95_ms"]),
            _number(row["p99_ms"]),
            _number(row["input_tokens"]),
            _number(row["output_tokens"]),
            _number(row["null_token_rows"]),
        ]
        for row in summary["operations"]
    ]
    lines.extend(
        _markdown_table(
            (
                "Operation",
                "Count",
                "Errors",
                "Error rate",
                "Attempts",
                "P50 ms",
                "P95 ms",
                "P99 ms",
                "Input tokens",
                "Output tokens",
                "Rows with null tokens",
            ),
            operation_rows,
        )
    )
    lines.extend(["", "## Estimated list-price cost by operation", ""])
    operation_cost_rows = [
        [
            row["operation"],
            row["provider"],
            row["model"],
            _price(row["amount"]),
            _number(row["priced_rows"]),
            _number(row["no_price_rows"]),
            _number(row["missing_token_rows"]),
        ]
        for row in summary["operation_costs"]
    ]
    lines.extend(
        _markdown_table(
            (
                "Operation",
                "Provider",
                "Model",
                "Estimate",
                "Priced rows",
                "Unpriced rows",
                "Null-token rows",
            ),
            operation_cost_rows,
        )
    )
    lines.extend(["", "## Estimated list-price cost per query", ""])
    query_cost_rows = [
        [
            row["correlation_id"],
            _number(row["operations"]),
            _price(row["amount"]),
            _number(row["priced_rows"]),
            _number(row["no_price_rows"]),
            _number(row["missing_token_rows"]),
        ]
        for row in summary["query_costs"]
    ]
    lines.extend(
        _markdown_table(
            (
                "Correlation ID",
                "Operations",
                "Estimate",
                "Priced rows",
                "Unpriced rows",
                "Null-token rows",
            ),
            query_cost_rows,
        )
    )
    lines.extend(
        [
            "",
            "## Outcomes",
            "",
            f"Investigations: {summary['investigation_count']}; degraded: "
            f"{summary['degraded_count']} ({_percent(summary['degraded_rate'])}).",
            "",
        ]
    )
    lines.extend(
        _markdown_table(
            ("Outcome", "Count", "Rate"),
            [
                [row["outcome"], _number(row["count"]), _percent(row["rate"])]
                for row in summary["outcomes"]
            ],
        )
    )
    cache = summary["cache"]
    lines.extend(
        [
            "",
            "## Query-embedding cache",
            "",
            f"Hits: {cache['hits']}; misses: {cache['misses']}; successful lookups: "
            f"{cache['successful_lookups']}; failed lookups: {cache['failed_lookups']}; "
            f"hit rate: {_percent(cache['hit_rate'])}.",
            "",
            "Observed (free tier): USD 0.00 (not combined with estimated list-price cost).",
            "",
            *_method_lines(summary),
        ]
    )
    return "\n".join(lines)


def format_operational_text(summary: Mapping[str, Any]) -> str:
    """Format the operational report as deterministic plain text."""

    lines = ["Provider operational metrics"]
    if summary["generated_at"] is not None:
        lines.append(f"Generated at: {summary['generated_at']}")
    lines.extend(
        [
            f"Time window: last {summary['since_hours']} hours.",
            f"Provider usage rows: {summary['usage_row_count']}.",
        ]
    )
    if not summary["usage_row_count"] and not summary["investigation_count"]:
        lines.append(EMPTY_REPORT)
    lines.append("Per-operation metrics:")
    for row in summary["operations"]:
        lines.append(
            f"{row['operation']}: count={row['count']}, errors={row['errors']}, "
            f"error_rate={_percent(row['error_rate'])}, attempts={row['attempts']}, "
            f"p50/p95/p99_ms={_number(row['p50_ms'])}/{_number(row['p95_ms'])}/"
            f"{_number(row['p99_ms'])}, input_tokens={row['input_tokens']}, "
            f"output_tokens={row['output_tokens']}, null_token_rows={row['null_token_rows']}"
        )
    lines.append("Estimated list-price cost by operation:")
    for row in summary["operation_costs"]:
        lines.append(
            f"{row['operation']} {row['provider']} {row['model']}: "
            f"{_price(row['amount'])}; priced={row['priced_rows']}, "
            f"unpriced={row['no_price_rows']}, null_tokens={row['missing_token_rows']}"
        )
    lines.append("Estimated list-price cost per query:")
    for row in summary["query_costs"]:
        lines.append(
            f"{row['correlation_id']}: {_price(row['amount'])}; "
            f"priced={row['priced_rows']}, unpriced={row['no_price_rows']}, "
            f"null_tokens={row['missing_token_rows']}"
        )
    lines.append(
        f"Degraded outcomes: {summary['degraded_count']}/{summary['investigation_count']} "
        f"({_percent(summary['degraded_rate'])})."
    )
    cache = summary["cache"]
    lines.append(
        f"Query-embedding cache: hits={cache['hits']}, misses={cache['misses']}, "
        f"successful_lookups={cache['successful_lookups']}, "
        f"failed_lookups={cache['failed_lookups']}, hit_rate={_percent(cache['hit_rate'])}"
    )
    lines.extend(_method_lines(summary))
    return "\n".join(lines)
