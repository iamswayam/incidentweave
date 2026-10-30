# Provider Usage Log

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

Aggregates are grouped by provider, model, operation tag, status, and error class.
They include row count, total attempts, average and nearest-rank p95 latency, and
summed input/output tokens. Missing token values contribute zero to sums; missing
latencies are excluded from latency statistics.

## What is logged

Classified provider errors and cooldown refusals are logged as failures. Deadline
timeouts use the `timeout` error class. Unexpected non-provider exceptions, such
as `ValueError`, are not recorded. Attempts count started provider attempts, and
latency is measured around the adapter call, excluding rate-limiter waiting.
Token counts are logged only when Gemini reports integer prompt and candidate
token counts.

Treat the database report as operational metadata: restrict database access and
avoid adding sensitive payload fields to this schema.
