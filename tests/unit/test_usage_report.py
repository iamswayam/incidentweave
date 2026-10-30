from __future__ import annotations

from app.providers.usage_report import (
    EMPTY_REPORT,
    format_markdown,
    format_text,
    summarize,
)


def _row(**overrides: object) -> dict[str, object]:
    row: dict[str, object] = {
        "provider": "gemini",
        "model": "gemini-test",
        "operation_tag": "generation",
        "status": "success",
        "error_class": None,
        "attempt_count": 1,
        "latency_ms": 100,
        "input_tokens": 10,
        "output_tokens": 5,
    }
    row.update(overrides)
    return row


def test_summarize_empty_rows_and_empty_formatters() -> None:
    summary = summarize([])

    assert summary == {"groups": []}
    assert format_text(summary) == EMPTY_REPORT
    assert format_markdown(summary) == EMPTY_REPORT


def test_summarize_groups_failures_and_sums_optional_values() -> None:
    summary = summarize(
        [
            _row(
                status="failure",
                error_class="server_error",
                attempt_count=3,
                latency_ms=None,
                input_tokens=None,
                output_tokens=4,
            ),
            _row(
                status="failure",
                error_class="server_error",
                attempt_count=2,
                latency_ms=20,
                input_tokens=7,
                output_tokens=None,
            ),
        ]
    )

    assert summary["groups"] == [
        {
            "provider": "gemini",
            "model": "gemini-test",
            "operation_tag": "generation",
            "status": "failure",
            "error_class": "server_error",
            "count": 2,
            "total_attempts": 5,
            "average_latency_ms": 20,
            "p95_latency_ms": 20,
            "input_tokens": 7,
            "output_tokens": 4,
        }
    ]


def test_p95_uses_nearest_rank_for_tied_top_values() -> None:
    rows = [_row(latency_ms=latency) for latency in range(1, 19)]
    rows.extend((_row(latency_ms=19), _row(latency_ms=19)))

    group = summarize(rows)["groups"][0]

    assert group["count"] == 20
    assert group["p95_latency_ms"] == 19
    assert group["average_latency_ms"] == 10.45


def test_none_latency_is_skipped_for_latency_aggregates() -> None:
    group = summarize([_row(latency_ms=None)])["groups"][0]

    assert group["average_latency_ms"] is None
    assert group["p95_latency_ms"] is None


def test_text_and_markdown_formatters_include_failure_group() -> None:
    summary = summarize(
        [
            _row(
                status="failure",
                error_class="server_error",
                attempt_count=3,
                latency_ms=None,
                input_tokens=None,
                output_tokens=None,
            )
        ]
    )

    text = format_text(summary)
    markdown = format_markdown(summary)

    assert "server_error" in text
    assert "3" in text
    assert "| Provider | Model | Operation | Status | Error class |" in markdown
    assert "| gemini | gemini-test | generation | failure | server_error |" in markdown
