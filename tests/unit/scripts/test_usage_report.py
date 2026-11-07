from __future__ import annotations

import asyncio

from scripts import usage_report


def test_output_option_writes_markdown_without_implicit_generation_time(
    monkeypatch,
    tmp_path,
) -> None:
    async def load_rows(since_hours: int):
        assert since_hours == 24
        return (
            [
                {
                    "provider": "gemini",
                    "model": "gemini-3.5-flash-lite",
                    "operation_tag": "generation",
                    "status": "success",
                    "error_class": None,
                    "attempt_count": 1,
                    "latency_ms": 12,
                    "input_tokens": 10,
                    "output_tokens": 5,
                    "correlation_id": "test-query",
                }
            ],
            [],
        )

    monkeypatch.setattr(usage_report, "_load_operational_rows", load_rows)
    output = tmp_path / "report.md"
    args = usage_report._parser().parse_args(["--since-hours", "24", "--output", str(output)])

    assert asyncio.run(usage_report._run(args)) == 0
    report = output.read_text(encoding="utf-8")
    assert report.startswith("# Provider operational metrics")
    assert "Generated at:" not in report
    assert "generation" in report
