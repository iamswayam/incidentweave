"""Pure aggregation and formatting for operational provider metrics."""

from __future__ import annotations

import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.providers.pricing import PRICING_TABLE, ModelPricing

MetricRow = dict[str, Any]


def nearest_rank(values: Sequence[int], percentile: int) -> int | None:
    """Return the nearest-rank percentile (ceil(p*n), one-based), or None when empty."""

    if not values:
        return None
    if not 1 <= percentile <= 100:
        raise ValueError("percentile must be between 1 and 100")
    ordered = sorted(values)
    return ordered[math.ceil(percentile * len(ordered) / 100) - 1]


def _cost(
    rows: Sequence[MetricRow],
    prices: Mapping[tuple[str, str], ModelPricing],
) -> dict[str, Any]:
    total = Decimal(0)
    priced_rows = 0
    missing_token_rows = 0
    no_price_rows = 0
    for row in rows:
        model_name = str(row["model"]).removeprefix("models/")
        model_pricing = prices.get((str(row["provider"]), model_name))
        input_tokens = row.get("input_tokens")
        output_tokens = row.get("output_tokens")
        output_is_required = model_pricing is None or model_pricing.output_tokens_billable
        missing_tokens = input_tokens is None or (output_is_required and output_tokens is None)
        if missing_tokens:
            missing_token_rows += 1
        if model_pricing is None or model_pricing.input_per_million is None:
            no_price_rows += 1
            continue
        if missing_tokens:
            continue
        row_cost = Decimal(input_tokens) * model_pricing.input_per_million
        if model_pricing.output_tokens_billable:
            if model_pricing.output_per_million is None:
                no_price_rows += 1
                continue
            row_cost += Decimal(output_tokens) * model_pricing.output_per_million
        total += row_cost / Decimal(1_000_000)
        priced_rows += 1
    return {
        "amount": total if priced_rows else None,
        "priced_rows": priced_rows,
        "missing_token_rows": missing_token_rows,
        "no_price_rows": no_price_rows,
    }


def _cache_metrics(investigations: Sequence[MetricRow]) -> dict[str, Any]:
    hits = 0
    misses = 0
    failed_lookups = 0
    for row in investigations:
        trace = row.get("trace")
        if not isinstance(trace, Mapping):
            continue
        cache = trace.get("query_embedding_cache", trace.get("cache"))
        if not isinstance(cache, Mapping):
            continue
        if cache.get("lookup_succeeded") is False:
            failed_lookups += 1
        elif cache.get("lookup_succeeded") is True:
            if cache.get("hit") is True:
                hits += 1
            elif cache.get("miss") is True:
                misses += 1
    lookups = hits + misses
    return {
        "hits": hits,
        "misses": misses,
        "successful_lookups": lookups,
        "failed_lookups": failed_lookups,
        "hit_rate": Decimal(hits) / Decimal(lookups) if lookups else None,
    }


def summarize_operational_metrics(
    usage_rows: Sequence[MetricRow],
    investigation_rows: Sequence[MetricRow],
    *,
    since_hours: int,
    generated_at: datetime | None = None,
    prices: Mapping[tuple[str, str], ModelPricing] = PRICING_TABLE,
) -> dict[str, Any]:
    """Aggregate provider calls, costs, persisted outcomes and cache traces."""

    by_operation: dict[str, list[MetricRow]] = defaultdict(list)
    cost_groups: dict[tuple[str, str, str], list[MetricRow]] = defaultdict(list)
    query_groups: dict[str, list[MetricRow]] = defaultdict(list)
    for row in usage_rows:
        operation = str(row["operation_tag"])
        provider = str(row["provider"])
        model = str(row["model"])
        by_operation[operation].append(row)
        cost_groups[(operation, provider, model)].append(row)
        query_groups[str(row.get("correlation_id") or "unattributed")].append(row)

    operations: list[MetricRow] = []
    for operation in sorted(by_operation):
        rows = by_operation[operation]
        latencies = [int(row["latency_ms"]) for row in rows if row.get("latency_ms") is not None]
        errors = sum(row["status"] == "failure" for row in rows)
        operations.append(
            {
                "operation": operation,
                "count": len(rows),
                "errors": errors,
                "error_rate": Decimal(errors) / Decimal(len(rows)),
                "attempts": sum(int(row.get("attempt_count") or 0) for row in rows),
                "p50_ms": nearest_rank(latencies, 50),
                "p95_ms": nearest_rank(latencies, 95),
                "p99_ms": nearest_rank(latencies, 99),
                "latency_rows_excluded": len(rows) - len(latencies),
                "input_tokens": sum(
                    int(row["input_tokens"]) for row in rows if row.get("input_tokens") is not None
                ),
                "output_tokens": sum(
                    int(row["output_tokens"])
                    for row in rows
                    if row.get("output_tokens") is not None
                ),
                "null_token_rows": sum(
                    row.get("input_tokens") is None or row.get("output_tokens") is None
                    for row in rows
                ),
            }
        )

    operation_costs = [
        {
            "operation": operation,
            "provider": provider,
            "model": model,
            **_cost(rows, prices),
        }
        for (operation, provider, model), rows in sorted(cost_groups.items())
    ]
    query_costs = [
        {
            "correlation_id": correlation_id,
            "operations": len({str(row["operation_tag"]) for row in rows}),
            **_cost(rows, prices),
        }
        for correlation_id, rows in sorted(query_groups.items())
    ]

    outcomes: dict[str, int] = {}
    for row in investigation_rows:
        outcome = str(row["outcome"])
        outcomes[outcome] = outcomes.get(outcome, 0) + 1
    total_investigations = len(investigation_rows)
    degraded = outcomes.get("generation_unavailable", 0) + outcomes.get("embedding_unavailable", 0)
    outcome_rows = [
        {
            "outcome": outcome,
            "count": count,
            "rate": Decimal(count) / Decimal(total_investigations),
        }
        for outcome, count in sorted(outcomes.items())
    ]
    return {
        "since_hours": since_hours,
        "generated_at": generated_at.isoformat() if generated_at is not None else None,
        "usage_row_count": len(usage_rows),
        "investigation_count": total_investigations,
        "operations": operations,
        "operation_costs": operation_costs,
        "query_costs": query_costs,
        "outcomes": outcome_rows,
        "degraded_count": degraded,
        "degraded_rate": (
            Decimal(degraded) / Decimal(total_investigations) if total_investigations else None
        ),
        "cache": _cache_metrics(investigation_rows),
        "missing_token_rows": sum(
            row.get("input_tokens") is None or row.get("output_tokens") is None
            for row in usage_rows
        ),
    }
