from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.providers.operational_metrics import (
    nearest_rank,
    summarize_operational_metrics,
)
from app.providers.operational_report import format_operational_markdown
from app.providers.pricing import ModelPricing


def _usage_row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "provider": "gemini",
        "model": "gemini-3.5-flash-lite",
        "operation_tag": "generation",
        "status": "success",
        "error_class": None,
        "attempt_count": 1,
        "latency_ms": 10,
        "input_tokens": 1_000,
        "output_tokens": 500,
        "correlation_id": "query-1",
    }
    row.update(overrides)
    return row


def _investigation(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {"outcome": "answered", "trace": None}
    row.update(overrides)
    return row


def test_nearest_rank_percentiles_for_small_and_large_samples() -> None:
    assert nearest_rank([9], 50) == 9
    assert nearest_rank([9, 1], 50) == 1
    assert nearest_rank([1, 2, 3, 4, 5], 50) == 3
    values = list(range(1, 101))
    assert nearest_rank(values, 50) == 50
    assert nearest_rank(values, 95) == 95
    assert nearest_rank(values, 99) == 99
    assert nearest_rank([], 95) is None


def test_null_latency_and_tokens_are_excluded_and_counted() -> None:
    summary = summarize_operational_metrics(
        [_usage_row(latency_ms=None, input_tokens=None, output_tokens=5)],
        [],
        since_hours=24,
    )

    operation = summary["operations"][0]
    assert operation["p50_ms"] is None
    assert operation["p95_ms"] is None
    assert operation["p99_ms"] is None
    assert operation["latency_rows_excluded"] == 1
    assert operation["null_token_rows"] == 1
    assert summary["missing_token_rows"] == 1
    assert summary["operation_costs"][0]["missing_token_rows"] == 1


def test_empty_rows_keep_rates_undefined_and_report_counts_zero() -> None:
    summary = summarize_operational_metrics([], [], since_hours=0)

    assert summary["usage_row_count"] == 0
    assert summary["operations"] == []
    assert summary["degraded_rate"] is None
    assert summary["cache"]["hit_rate"] is None
    assert format_operational_markdown(summary).startswith("# Provider operational metrics")


def test_cost_arithmetic_and_unpriced_models_are_separate() -> None:
    pricing = {
        ("gemini", "priced-model"): ModelPricing(
            input_per_million=Decimal("2"),
            output_per_million=Decimal("4"),
            output_tokens_billable=True,
            currency="USD",
            source_url="https://example.test/pricing",
            retrieved_on="2026-11-07",
            free_tier_note="test",
        )
    }
    rows = [
        _usage_row(model="priced-model", input_tokens=1_000_000, output_tokens=500_000),
        _usage_row(model="unpriced-model", correlation_id="query-2"),
    ]

    summary = summarize_operational_metrics(rows, [], since_hours=24, prices=pricing)

    priced = next(row for row in summary["operation_costs"] if row["model"] == "priced-model")
    unpriced = next(row for row in summary["operation_costs"] if row["model"] == "unpriced-model")
    assert priced["amount"] == Decimal("4")
    assert priced["priced_rows"] == 1
    assert unpriced["amount"] is None
    assert unpriced["no_price_rows"] == 1


def test_cache_hit_rate_and_degraded_outcome_rates() -> None:
    summary = summarize_operational_metrics(
        [],
        [
            _investigation(
                trace={
                    "query_embedding_cache": {
                        "hit": True,
                        "miss": False,
                        "lookup_succeeded": True,
                    }
                }
            ),
            _investigation(
                outcome="generation_unavailable",
                trace={"cache": {"hit": False, "miss": True, "lookup_succeeded": True}},
            ),
            _investigation(outcome="embedding_unavailable"),
            _investigation(
                outcome="error",
                trace={"cache": {"hit": False, "miss": False, "lookup_succeeded": False}},
            ),
        ],
        since_hours=24,
    )

    assert summary["cache"] == {
        "hits": 1,
        "misses": 1,
        "successful_lookups": 2,
        "failed_lookups": 1,
        "hit_rate": Decimal("0.5"),
    }
    assert summary["degraded_count"] == 2
    assert summary["degraded_rate"] == Decimal("0.5")
    assert {row["outcome"]: row["rate"] for row in summary["outcomes"]} == {
        "answered": Decimal("0.25"),
        "error": Decimal("0.25"),
        "embedding_unavailable": Decimal("0.25"),
        "generation_unavailable": Decimal("0.25"),
    }


def test_markdown_is_byte_identical_for_repeated_inputs() -> None:
    rows = [
        _usage_row(
            status="failure",
            error_class="timeout",
            attempt_count=2,
            latency_ms=21,
            correlation_id="stable-query",
        ),
        _usage_row(latency_ms=11, correlation_id="stable-query"),
    ]
    investigations = [
        _investigation(
            trace={
                "query_embedding_cache": {
                    "hit": False,
                    "miss": True,
                    "lookup_succeeded": True,
                }
            }
        )
    ]
    at = datetime(2026, 11, 7, tzinfo=UTC)
    summary = summarize_operational_metrics(rows, investigations, since_hours=24, generated_at=at)
    first = format_operational_markdown(summary)
    second = format_operational_markdown(summary)

    assert first.encode("utf-8") == second.encode("utf-8")
    assert "Generated at: 2026-11-07T00:00:00+00:00" in first
    operation = summary["operations"][0]
    assert (operation["p50_ms"], operation["p95_ms"], operation["p99_ms"]) == (11, 21, 21)
    assert operation["errors"] == 1
    assert operation["error_rate"] == Decimal("0.5")


def test_unknown_models_render_no_official_price() -> None:
    summary = summarize_operational_metrics(
        [_usage_row(model="unpublished-model")],
        [],
        since_hours=24,
    )

    report = format_operational_markdown(summary)

    assert "no official price" in report
    assert "Observed (free tier): USD 0.00" in report
