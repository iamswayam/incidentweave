# Degraded modes and query-embedding cache

**As of 2026-11-01.**

This runbook describes the application behavior implemented by the investigation pipeline,
API, provider usage logger, and persistent query-embedding cache. The LLM gateway is not part
of the current runtime; the provider-layer decision is recorded in
[09-llm-gateway-decision.md](../architecture-review/09-llm-gateway-decision.md).

## Outcomes

The API returns HTTP 200 for both explicit degraded outcomes. Clients must inspect `outcome`,
`degraded`, and `degraded_reason`, not infer success from the HTTP status.

| Outcome | API response | CLI output | Persisted audit |
|---|---|---|---|
| `generation_unavailable` | `outcome="generation_unavailable"`, `unavailable_answer=true`, `degraded=true`, and `degraded_reason="generation_unavailable"`. Diagnosis, claims, and cited chunk IDs are empty; ranked metadata-only evidence is returned after the evidence guard accepted retrieval. Model self-rating is not applicable. | Prints `Outcome`, `Diagnosis`, `Unavailable answer`, `Degraded`, and `Degraded reason`; it does not print a generated answer. | `investigations.outcome` records the outcome. `audit_records.tool_calls.degraded` stores the degraded flags/reason, evidence, and evidence-check state; `audit_records.trace` stores the generation trace. Degraded persistence omits prompt and source text. |
| `embedding_unavailable` | `outcome="embedding_unavailable"`, `unavailable_answer=true`, `degraded=true`, and `degraded_reason="embedding_unavailable"`. It returns sanitized lexical-only metadata and an empty diagnosis; `evidence_check.is_sufficient` is null with reason `not evaluated: no query embedding`. The vector evidence guard is not evaluated and generation is not attempted. | Prints the same outcome/degraded fields and no diagnosis. | `investigations.outcome` records the outcome. `audit_records.tool_calls.degraded` stores the degraded reason and evidence-check state; `audit_records.trace` records lexical retrieval mode and provider/cache trace when available. It does not retain prompt or source text for this degraded response. |

`GET /investigations/{id}` reconstructs persisted degraded outcomes. An embedding cache
read failure is not itself proof of a provider outage; check the audit trace and usage records
to identify the actual failed stage.

## Finding the cause

1. If provider usage logging is enabled, inspect `provider_usage_log` for the request's
   `correlation_id`. Useful columns are `provider`, `model`, `operation_tag`, `status`,
   `error_class`, `attempt_count`, `latency_ms`, and `correlation_id`. Usage logging is
   controlled by `PROVIDER_USAGE_LOG_ENABLED` and defaults to disabled.
2. Inspect the associated `audit_records` row. Its `trace` JSON may include
   `failed_stage`, `provider_attempts`, `error_classes`, `attempt_count`, `elapsed_ms`,
   `cache`, `retrieval_mode`, and `correlation_id`. The `tool_calls` JSON includes the
   degraded reason, metadata-only evidence, and evidence-check state. Fields depend on the
   path; absent fields are not evidence of success.
3. Cache read and write failures emit warning logs with the exception class only:
   `Query embedding cache read failed (<class>)` and
   `Query embedding cache write failed (<class>)`. The log message does not include query
   text or the exception message.

The audit table is `audit_records`; the query-embedding cache is
`query_embedding_cache`. These read-only queries inspect metadata without selecting query
text or vectors:

```sql
SELECT id, investigation_id, trace, tool_calls, created_at
FROM audit_records
WHERE investigation_id = 123
ORDER BY created_at DESC;

SELECT provider, model, operation_tag, status, error_class, attempt_count,
       latency_ms, correlation_id, created_at
FROM provider_usage_log
WHERE correlation_id = 'replace-with-correlation-id'
ORDER BY created_at DESC;
```

Replace the example identifiers with the investigation and correlation IDs for the incident.
The provider-usage query returns no rows when usage logging is disabled or no record was
written. Do not query or print credentials.

## Groq generation fallback

The optional Groq path is generation-only and is disabled by default.

| Setting | Purpose |
|---|---|
| `GROQ_FALLBACK_ENABLED` | Explicit opt-in; default `false`. |
| `GROQ_API_KEY` | Groq credential, kept only in the ignored local `.env`/environment. |
| `GROQ_MODEL` | Explicit fallback model identifier. |
| `GROQ_TIMEOUT_SECONDS` | Request timeout; default 60 seconds. |
| `GROQ_RATE_LIMIT_RPM`, `GROQ_RATE_LIMIT_TPM`, `GROQ_RATE_LIMIT_RPD` | Optional local request/token/day ceilings. |
| `GROQ_COOLDOWN_FAILURES`, `GROQ_COOLDOWN_SECONDS` | Optional cooldown trigger and duration. |

Before enabling it, review the current Groq data terms and limitations and validate the model
on the registered golden set. See [the provider note](../notes/13-groq-generation-fallback.md).
The application does not automatically rotate provider keys.

## Query-embedding cache

The table stores the embedding model, task type, dimensions, SHA-256 hash of a
whitespace-normalized case-preserved query, JSON vector, and creation time. It does **not**
store query text. The key is `(embedding_model, task_type, dimensions, query_hash)`.
Entries older than 30 days are expired; insertion evicts oldest rows to keep the table at
10,000 rows. Hashes and vectors remain sensitive derived data.

Inspect the number and age of rows without reading vectors:

```sql
SELECT count(*) AS row_count, min(created_at) AS oldest, max(created_at) AS newest
FROM query_embedding_cache;

SELECT embedding_model, task_type, dimensions, count(*) AS row_count
FROM query_embedding_cache
GROUP BY embedding_model, task_type, dimensions
ORDER BY embedding_model, task_type, dimensions;
```

To clear the cache intentionally, run the following against the intended local database and
commit the transaction:

```sql
BEGIN;
DELETE FROM query_embedding_cache;
COMMIT;
```

Do not delete the table or its migration. Cache read/write warnings report only the exception
class; a successful cache read is not logged per query.

## Migrations and quota exhaustion

Apply the current schema with:

```powershell
alembic upgrade head
```

If a provider quota is exhausted, use the typed error/usage trace to confirm the provider and
operation, stop repeated manual runs, and wait for the applicable quota window or use an
explicitly approved provider configuration. Do not create or rotate keys to evade quotas.
There is no automatic cross-model embedding fallback; do not substitute another model's
vectors for the indexed Gemini vectors.

## Verified limits

- The current code does not route through LiteLLM; no gateway-down behavior is implemented.
- Exact provider quota reset times and free-tier limits are provider policies and are not
  verified here.
- Whether a particular audit field is populated depends on the failure path and persistence
  setting.
