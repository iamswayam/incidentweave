# Provider Usage Log

**As of 2026-11-07.**

## Purpose and privacy

The provider usage log records operational metadata so provider failures, latency,
attempts, and token usage can be reviewed without retaining request content. The
`provider_usage_log` table contains:

| Column | Meaning |
|---|---|
| `id` | Row identifier |
| `provider`, `model` | Provider and model names |
| `operation_tag` | One of the supported operation categories |
| `status`, `error_class` | Success or failure and the classified failure, when present |
| `attempt_count` | Provider attempts started |
| `latency_ms` | Elapsed adapter time in milliseconds |
| `input_tokens`, `output_tokens` | Provider-reported token counts, when integer values are available |
| `correlation_id` | Investigation trace ID or a generated ID for standalone calls |
| `created_at` | Database insertion time |

No prompt, response, source-code text, API key, or other payload is stored in this
table. Logging is disabled by default.

## Enable logging

Set `PROVIDER_USAGE_LOG_ENABLED=true` in `.env` to enable logging. Database writes
are bounded by `PROVIDER_USAGE_LOG_TIMEOUT_SECONDS` (default `2` seconds); a timed
out write is warned and does not change the provider result or exception. Then
apply the schema:

```powershell
.\.venv\Scripts\python.exe -m alembic upgrade head
```

Provider usage writes use a separate short database session. Write failures are
warned by exception class only and do not replace the provider call's result or
exception.

## Operation tags and correlation

Supported tags are `query_embedding`, `document_embedding`, `generation`,
`experiment_embedding`, and `evaluation`. A `usage_operation(tag)` context overrides
the call-site tag for its duration; otherwise the explicit call-site tag is used.
The investigation flow reuses its existing correlation ID. Standalone provider
calls without that context receive a generated UUID.

## Report

The report reads usage rows and does not write to the database. Text output:

```powershell
.\.venv\Scripts\python.exe -m scripts.usage_report --since-hours 24
```

Markdown output:

```powershell
.\.venv\Scripts\python.exe -m scripts.usage_report --since-hours 24 --format markdown
```

The command reports operation-level metrics, list-price estimates, investigation
outcomes, and query-embedding cache statistics as described below. It is read-only
and does not call provider APIs.

## Operational metrics report

The operational report summarizes provider usage rows by operation. Counts are
logged provider calls; errors are rows with `status=failure`; attempts are summed
`attempt_count`; token totals sum the available logged input and output tokens.
Latency p50/p95/p99 use the nearest-rank method: sort non-null latencies and select
the value at one-based rank `ceil(p*n)`. Missing latency values are excluded.

Degraded counts and rates come from persisted investigation outcomes
`generation_unavailable` and `embedding_unavailable`; each investigation is counted
once, and the rate denominator is all unique investigations in the selected time
window. Query-embedding cache hits, misses, and failed lookups use the trace from the
latest audit row for each investigation. Only successful lookups are included in the
hit-rate denominator; when there are no successful lookups, the rate is reported as
`-`.

Estimated list-price cost per operation and correlation ID (query) multiplies the
logged token counts by the published rates in the
[pricing table](../../app/providers/pricing.py). It is an estimate, not a billing
record. Rows missing a token count required by that model's price are excluded and
counted. Models without a published price are shown as “no official price.”
“Observed (free tier)” is shown separately as USD 0.00 if usage is covered by the
free tier; provider billing actuals are not ingested or verified. The estimate
and observed figure are never added.

The pricing table records provider, model, currency, input/output price per million
tokens, source URL, retrieval date, and a text-only free-tier note. As of
2026-11-07, the configured Gemini model price rows could not be read from the
[official Google AI Studio pricing page](https://aistudio.google.com/docs/pricing),
so both remain unpriced. The page's general Free-tier text says “Limited access to
certain models” and “Free input & output tokens”; model-specific eligibility could
not be read. To update a price, change the entry, its official source URL,
`retrieved_on`, and model-specific free-tier note together.

Generate a Markdown report with:

```powershell
.\.venv\Scripts\python.exe -m scripts.usage_report --since-hours 24 --format markdown --output usage-report.md
```

The report is deterministic for the same rows and does not include a generation
timestamp unless one is explicitly supplied to the formatter.

## What is logged

Classified provider errors and cooldown refusals are logged as failures. Deadline
timeouts use the `timeout` error class. Unexpected non-provider exceptions, such
as `ValueError`, are not recorded. Attempts count started provider attempts, and
latency is measured around the adapter call, excluding rate-limiter waiting.
Token counts are logged only when Gemini or Groq reports integer prompt and
completion token counts.

Treat the database report as operational metadata: restrict database access and
avoid adding sensitive payload fields to this schema.
