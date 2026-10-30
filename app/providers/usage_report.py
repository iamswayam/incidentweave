"""Pure aggregation and formatting helpers for provider usage reports."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Sequence
from typing import Any

EMPTY_REPORT = "No provider usage recorded in the selected period."

Group = dict[str, Any]
Summary = dict[str, list[Group]]


def summarize(rows: Sequence[dict[str, Any]]) -> Summary:
    """Aggregate provider usage rows by provider, model, operation and outcome."""

    grouped: dict[tuple[str, str, str, str, str | None], list[dict[str, Any]]] = (
        defaultdict(list)
    )
    for row in rows:
        key = (
            str(row["provider"]),
            str(row["model"]),
            str(row["operation_tag"]),
            str(row["status"]),
            row["error_class"],
        )
        grouped[key].append(row)

    groups: list[Group] = []
    for key in sorted(
        grouped,
        key=lambda item: (*item[:4], item[4] or ""),
    ):
        grouped_rows = grouped[key]
        latencies = sorted(
            row["latency_ms"]
            for row in grouped_rows
            if row["latency_ms"] is not None
        )
        p95_latency = (
            latencies[math.ceil(0.95 * len(latencies)) - 1]
            if latencies
            else None
        )
        groups.append(
            {
                "provider": key[0],
                "model": key[1],
                "operation_tag": key[2],
                "status": key[3],
                "error_class": key[4],
                "count": len(grouped_rows),
                "total_attempts": sum(
                    row["attempt_count"] for row in grouped_rows
                ),
                "average_latency_ms": (
                    sum(latencies) / len(latencies) if latencies else None
                ),
                "p95_latency_ms": p95_latency,
                "input_tokens": sum(
                    row["input_tokens"] or 0 for row in grouped_rows
                ),
                "output_tokens": sum(
                    row["output_tokens"] or 0 for row in grouped_rows
                ),
            }
        )
    return {"groups": groups}


def _display(value: object) -> str:
    return "-" if value is None else str(value)


def format_text(summary: Summary) -> str:
    """Format an aggregate as a plain-text table."""

    groups = summary["groups"]
    if not groups:
        return EMPTY_REPORT
    header = (
        "provider | model | operation | status | error_class | count | "
        "attempts | avg_latency_ms | p95_latency_ms | input_tokens | output_tokens"
    )
    rows = [
        " | ".join(
            (
                _display(group["provider"]),
                _display(group["model"]),
                _display(group["operation_tag"]),
                _display(group["status"]),
                _display(group["error_class"]),
                _display(group["count"]),
                _display(group["total_attempts"]),
                _display(group["average_latency_ms"]),
                _display(group["p95_latency_ms"]),
                _display(group["input_tokens"]),
                _display(group["output_tokens"]),
            )
        )
        for group in groups
    ]
    return "\n".join((header, *rows))


def format_markdown(summary: Summary) -> str:
    """Format an aggregate as a Markdown table."""

    groups = summary["groups"]
    if not groups:
        return EMPTY_REPORT
    headers = (
        "Provider",
        "Model",
        "Operation",
        "Status",
        "Error class",
        "Count",
        "Attempts",
        "Average latency (ms)",
        "P95 latency (ms)",
        "Input tokens",
        "Output tokens",
    )
    header = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join("---" for _ in headers) + " |"
    rows = [
        "| "
        + " | ".join(
            _display(value)
            for value in (
                group["provider"],
                group["model"],
                group["operation_tag"],
                group["status"],
                group["error_class"],
                group["count"],
                group["total_attempts"],
                group["average_latency_ms"],
                group["p95_latency_ms"],
                group["input_tokens"],
                group["output_tokens"],
            )
        )
        + " |"
        for group in groups
    ]
    return "\n".join((header, separator, *rows))
