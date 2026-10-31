# Provider layer design (item 18a-1)

## Scope

This note covers the design for the provider-layer direction approved on 2026-10-28. The repo is not implementing a LiteLLM gateway in this step. The goal is to design a thin provider layer that can later be pointed at a gateway without changing the app's call sites, graph, scripts or tests.

This document is a design-only record. No code, no compose change, no baseline, no gate and no manifest file is modified here.

## Inventory summary

The project makes Gemini provider calls today in four categories:

- generation: grounded answer generation via `app/investigation/generation.py`
- query embedding: `scripts/investigate.py` and `scripts/search_repo.py`
- repository/document embedding: `scripts/embed_chunks.py` and the evaluation embedding cache path
- experiment pacing: `evaluation/chunking_experiment.py` and `scripts/run_chunking_experiment.py` for `--batch-delay-seconds`

The direct call path is centralized in `app/providers/gemini.py`, which enforces the `x-goog-api-key` header and bounded retry logic. Higher layers mostly call it indirectly without custom retry logic. The API layer delegates to the investigation script, which then reaches the shared provider helper and the embedding helper.

## Call-site inventory

| Location | Function | Current model / call | Secret or key loading | Retry and error handling | Test replacement | CI / operational note |
|---|---|---|---|---|---|---|
| `app/providers/gemini.py` | `get_gemini_api_key()`, `send_once()`, `post_json()` | Shared Gemini HTTP helper for both generation and embedding calls. `post_json()` posts to a provider URL with `x-goog-api-key` header. | Reads `GEMINI_API_KEY` from the process environment via `os.getenv()` and raises if missing. | Retries on `429`, `500`, `502`, `503`, `504` with exponential backoff and jitter; has a whole-operation timeout; final failure redacts the key from the error text. Non-retryable HTTP errors are raised immediately. | Unit tests use `httpx.MockTransport` and monkeypatch env values; they assert the key is in the header and not in the URL. | CI does not require a live key or gateway. |
| `app/investigation/generation.py` | `generate_investigation()` | Model `gemini-3.5-flash-lite`; `:generateContent` endpoint | No direct key handling; calls the shared `post_json()` helper | No custom retry beyond the provider helper (`deadline_seconds=90`, `max_attempts=3`) | Tests monkeypatch `make_client()` and assert the request payload, schema and header | CI-safe and mocked |
| `app/investigation/graph.py` | `generate()` state node | Calls `generate_investigation()` as part of the LangGraph flow | Inherits provider key loading via shared helper | No custom retry; inherits helper behavior | Unit tests monkeypatch `generate_investigation` | CI-safe |
| `scripts/embed_chunks.py` | `embed_text()`, `embed_texts()`, `embed_repository_chunks()` | Model `models/gemini-embedding-001`, `outputDimensionality=768` | Shared helper loads `GEMINI_API_KEY` from env | Batch failures are caught and reported; dimension mismatch raises `ValueError` | Unit tests assert header and exact request bodies | CI-safe |
| `scripts/investigate.py` | `investigate_repository()` | Query embedding happens before retrieval and generation | Shared helper loads key | Outer timeout and persisted error record on failure | Integration tests stub `embed_text` and graph generation | No live provider dependency |
| `scripts/search_repo.py` | `main()`, `search_repository()` | Query embedding for a repo search | Shared helper | No custom retry; provider helper handles it | CLI flows are mocked or bypassed | CI-safe |
| `app/api.py` | `create_investigation()`, `get_investigation()` | Delegates to `investigate_repository()`, no direct provider call | No direct key handling | Converts provider or validation failures into HTTP errors | API tests assert response shape and error mapping | CI-safe |
| `evaluation/runner.py` | `load_key_without_logging()`, `cached_embedding()`, `_counted_send_once()` | Evaluation-only cache + generation throttle | Reads `.env` if needed and never logs the secret | `MIN_API_DELAY_SECONDS` pacing and generation budget; `429` is counted | Tests validate budget and cache logic | CI-safe |
| `evaluation/chunking_experiment.py` | `embed_missing()`, `_embed()` | Embedding batches with `--batch-delay-seconds` pacing | Reads env or settings | Pacing is implemented between batches; no explicit fallback | Unit tests validate schedule and cache ordering | Evaluation-only |
| `scripts/run_chunking_experiment.py` | `_embed()` CLI | Same as above | env / settings | Fails fast if key missing | Unit tests validate the CLI path | Not part of default CI |
| `tests/unit/providers/test_gemini_provider.py` | retry and redaction tests | Mocked provider contract | Sets `GEMINI_API_KEY` in env | Verifies retries and redaction | Canonical provider contract tests | CI-safe |
| `tests/unit/providers/test_gemini_api_key_header.py` | request-header tests | Mocked generation + embedding contract | Sets `GEMINI_API_KEY` in env | Asserts key is in header and not URL | Canonical replacement for provider | CI-safe |
| `tests/unit/test_chunking_experiment.py` | pacing tests | Mocked embed function | `monkeypatch.setenv` coupled with fake embed | Verifies delay between batches | Official pacing test replacement | CI-safe |

## Direction

DIRECTION (approved 2026-10-28): do not deploy the LiteLLM proxy now. Build our own thin provider layer and write it so a gateway can be plugged in later.

Reasons:

- the failures that hurt this app are not solved by a gateway; a Gemini outage should still return cited retrieved evidence
- pacing is a manual flag today; there is no caching policy in the runtime path to absorb a provider outage
- a proxy adds a new container, a new database, and a single point of failure on the critical path for one app run by one developer
- it inserts a translation layer between us and Gemini while item 14a needs Gemini embedding `task_type`, and LiteLLM proxy docs do not confirm that contract in the source we actually read
- every fallback model needs its own golden-set and citation validation either way

LiteLLM facts that stay true: spend tracking, admin UI, virtual keys, rate limits and fallbacks are open source; SSO is free up to 5 users; audit logs are enterprise; in March 2026, PyPI releases 1.82.7 and 1.82.8 were compromised, Docker proxy users were not affected, and v1.83.0 is the clean release. Gateway revisit triggers: three or more providers in real use, a wish for dashboard/key management, or a second service needing LLM access. If adopted later, the security rules in [09-llm-gateway-decision.md](09-llm-gateway-decision.md) remain valid.

## Layering

The provider layer sits between the app and the external provider. It is intentionally thin and wraps the current direct-client logic rather than replacing the application flow.

Provider interfaces:

- `generate()` for grounded answer generation
- `embed()` / `embed_many()` for document and query embeddings
- `classify_error()` for mapping raw HTTP statuses and exceptions to a stable failure taxonomy
- `RateLimiter` and `CooldownCircuit` for provider-level gating
- `UsageLogger` for provider telemetry without prompts or responses

The existing adapter is the current `app/providers/gemini.py` and it remains the first adapter. The app-facing function signatures stay exactly as they are today:

- `generate_investigation(prompt: str, *, temperature: float | None = None) -> tuple[dict[str, object], int]`
- `embed_text(text: str) -> list[float]`
- `embed_texts(texts: list[str]) -> list[list[float]]`

This keeps the graph, scripts and tests unchanged. The adapter is a thin wrapper that may later be replaced by a gateway-backed implementation or by another provider adapter without changing call sites.

No new dependency is introduced in this design. The provider layer stays on `httpx` and uses the current direct REST approach as the baseline contract.

## Error taxonomy and retryability

The provider layer must map provider failures to a fixed set of classes before any retry or fallback decision is made.

| Error class | Meaning | Retryable? | Notes |
|---|---|---|---|
| `rate_limited` | HTTP 429 or quota exhaustion | Yes | Retry with backoff; honour `Retry-After` when present, never depend on it |
| `server_error` | HTTP 5xx | Yes | Provider or upstream server failure that is retryable |
| `timeout` | request deadline exceeded or network time-out | Yes | Retry with same bounded deadline logic |
| `auth` | invalid or missing key / auth header | No | Fail explicitly, do not retry blindly |
| `bad_request` | invalid model / invalid payload / unsupported parameter | No | Structured payload or schema issue |
| `safety_blocked` | blocked by provider safety policy | No | Explicit failure, not a retry path |
| `schema_invalid` | returned JSON is malformed or schema validation fails | No | Fail explicitly and log the classification, not the response text |

The provider layer should classify first, then decide whether to retry. This is the same operational principle already used in `app/providers/gemini.py` today: bounded retries for timeout and retryable HTTP responses, while final non-retryable errors fail immediately.

## Retry ownership

The provider layer owns retries, not the calling graph or scripts. The current bounded backoff with jitter remains the base policy:

- exponential backoff with bounded jitter
- retry only on classified retryable failures
- honour `Retry-After` when the provider exposes it, but never depend on it for correctness
- keep the same whole-operation deadline semantics already in `post_json()`

This preserves the existing code contract while making the retry policy explicit and testable. The app should not retry the same failure again after the provider layer has already exhausted its policy; a repeated failure should be surfaced as an explicit upstream error to the caller.

## Per-provider rate limiter

A provider-specific rate limiter is a required part of the thin provider layer. It is separate from app-level pacing and should be async, config-driven and provider-aware.

Requirements:

- `RPM` = requests per minute
- `TPM` = tokens per minute
- `RPD` = requests per day
- limits are read from configuration, never hard-coded into logic
- the limiter works per provider, per model and per operation class
- the limiter must be conservative and fail closed when limits are unknown

This replaces the current manual pacing default without abandoning compatibility. Existing manual controls such as `--batch-delay-seconds` remain valid for compatibility and keeps the offline experiment path working, but the runtime code path should rely on the provider-layer limiter rather than ad-hoc delay flags.

## Cooldown and circuit breaker

The provider layer also needs a cooldown policy. After N consecutive retryable failures for a provider or a model, the provider enters a cooldown state for T seconds. The thresholds are configuration-driven and are not hard-coded in the app logic.

Suggested defaults (design only):

- consecutive retryable failures threshold: configuration value, not a constant in module code
- cooldown duration: configuration value, not a hard-coded assumption
- reset condition: success or timer expiry, depending on the provider policy

On cooldown, the provider layer must fail explicitly with a clear and classified error instead of silently offsetting to another provider or bypassing the layer. This keeps the app behavior deterministic and debuggable.

## Usage log table and report script

The usage log is the provider-layer telemetry table. It must store provider-level metadata but never prompt or response text, because prompts contain source code and responses may include repository code snippets.

| Column | Type | Notes |
|---|---|---|
| `provider` | string | e.g. `gemini` |
| `model` | string | provider model name |
| `operation_tag` | string | `query_embedding`, `document_embedding`, `generation`, `experiment_embedding`, `evaluation` |
| `status` | string | `success` or `failure` only |
| `error_class` | string or null | one of the provider error-taxonomy values; null on success |
| `attempt_count` | integer | number of retries attempted |
| `latency_ms` | integer or null | provider call latency |
| `input_tokens` | integer or null | if the provider reports it |
| `output_tokens` | integer or null | if the provider reports it |
| `correlation_id` | string | stable trace ID |
| `created_at` | timestamp | when the log row is written |

This table does not store raw prompt or response text or any code snippets. The design also includes a simple report script that reads this table, summarizes counts by provider/model/status, and emits a markdown or console report. That is a documentation-only design now; it does not require new app runtime code in this PR.

## Operation tags

Supported operation tags in the provider layer are:

- `query_embedding`
- `document_embedding`
- `generation`
- `experiment_embedding`
- `evaluation`

These tags differentiate offline evaluation, runtime queries, generation, and long-running embedding experiments. The report script can aggregate usage by tag to measure cost and failure patterns without storing human-code content.

## LLM response schema

LLM response schema changes are managed explicitly in code rather than by implicit model output. In this repo the generation schema is defined in `RESPONSE_SCHEMA` inside [../../app/investigation/generation.py](../../app/investigation/generation.py), and the tests assert the exact schema and payload shape in [../../tests/unit/providers/test_gemini_api_key_header.py](../../tests/unit/providers/test_gemini_api_key_header.py) and [../../tests/unit/providers/test_gemini_provider.py](../../tests/unit/providers/test_gemini_provider.py).

That means a provider schema change is recorded in code, checked by tests, and reviewed as a deliberate contract change. The repo does not rely on unspecified model drift or runtime-only schema assumptions.

## Database schema changes

Database schema changes are managed through Alembic migrations, not through ad hoc SQL or code-generated tables. The repository-specific settings are in [../../alembic.ini](../../alembic.ini), and the migration runner is [../../migrations/env.py](../../migrations/env.py). It reads the configured `DATABASE_URL`, converts PostgreSQL URLs to the async SQLAlchemy driver the app uses, and then runs `context.run_migrations()` against the project metadata defined from [../../app/db/base.py](../../app/db/base.py) and the modules under [../../app/db/models](../../app/db/models).

The migration revisions are numbered and named in timestamp order, for example:

- `20260819_0001_initial_schema.py`
- `20261024_0002_investigation_outcome.py`
- `20261025_0003_ingest_runs.py`
- `20261026_0004_replayable_audit.py`

Each file uses an Alembic `revision` and `down_revision` pair, so the history is linear and auditable. The latest revision in this repo is `20261026_0004_replayable_audit.py`; it added the replayable audit fields (`prompt`, `prompt_version`, `raw_response`, `raw_self_rating`, `generation_params`, `thresholds`, `embedding_model`, `chunk_records`, `trace`), and the current ORM model in [../../app/db/models/audit.py](../../app/db/models/audit.py) matches that migration history.

CI applies the migrations before test execution. In [../../.github/workflows/ci.yml](../../.github/workflows/ci.yml), the workflow provisions a PostgreSQL service, then runs `alembic upgrade head` before the offline retrieval gate and pytest. That is the verified CI path in this repo. The usage log table for 18a-3 is a new database change and should follow the same pattern: add an Alembic migration revision numbered `0005` and a corresponding ORM model in the app DB models package, with no prompt or response text columns stored in the usage table.

## Embeddings

The direct REST call supports Gemini task types natively. That is the contract that item 14a needs to use when it sets `task_type` for `RETRIEVAL_DOCUMENT` and `CODE_RETRIEVAL_QUERY` and keeps the embedding dimension at 768.

What we could verify in this repo:

- the current direct embedding flow in [../../scripts/embed_chunks.py](../../scripts/embed_chunks.py) posts a model plus `outputDimensionality` and expects a 768-length vector
- the app currently calls the direct Gemini REST API, not a proxy or gateway, for both query and document embeddings
- the project already records the need for `task_type` in item 14a and the design expects a native provider-level task-type contract

What we could not verify from a source we actually read in this session:

- whether LiteLLM proxy docs confirm support for Gemini embedding `task_type` in the exact pinned version we would choose later
- whether any LiteLLM-proxy-specific parameter mapping would alter the native Gemini API semantics

This is why the provider-layer design keeps the direct REST contract as the canonical implementation while deferring any gateway adoption until the actual gateway contract is confirmed.

## CI and tests

CI remains fully offline and mock-based. The existing pattern is already in the repo:

- mock `httpx.AsyncClient` with `httpx.MockTransport`
- set `GEMINI_API_KEY` in test env only when needed
- assert request header, request body and exact failure handling
- leave offline evaluation and the embedding cache unchanged

This design does not require a gateway or a live provider in CI. It keeps the same principle as the current code: tests replace the real provider and fail on a classification mismatch or a changed contract.

## Security

Keys are never logged or stored in the usage table. The provider layer keeps the current redaction behavior in `app/providers/gemini.py` and avoids writing prompt and response payloads to logs or usage tables because those may contain source code.

The design remains consistent with the secure handling already in the repo: environment-based keys, redacted errors, no secret values in the URL, no secret values in response logs and no prompt text in provider telemetry.

## Explicit failure behaviour

When the provider layer fails, the app fails explicitly. There is no success-shaped fallback in the provider layer itself. When generation fails, the app may return an explicit degraded response only after the maintainers approve the 18d design. Until then, the provider layer treats failure as an explicit failure and does not silently re-route or bypass the provider contract.

The proposed response contract, failure matrix, and approval checklist are in [the item 18d-1 degraded-response design](13-degraded-response-design.md). No degraded behavior is approved or implemented by that record.

## Maintainer decisions

- Direction approved: own thin provider layer now; no LiteLLM proxy deployment now.
- Model choices for fallbacks are decided in 18b with verification at build time.
- The API contract for degraded responses is decided in 18d design and requires maintainer approval before implementation.

## Implementation notes (item 18a-2)

- Code location: `app/providers/gemini.py` holds the typed provider exceptions, `AsyncRateLimiter`, `CooldownStateMachine`, `GeminiProviderAdapter.post_json`, and `guarded_post_json`.
- Wiring: `app/investigation/generation.py` and `scripts/embed_chunks.py` call `guarded_post_json`; the public `make_client` names and the generation/embedding function signatures remain unchanged.
- Settings: `PROVIDER_RATE_LIMIT_RPM`, `PROVIDER_RATE_LIMIT_TPM`, `PROVIDER_RATE_LIMIT_RPD`, `PROVIDER_COOLDOWN_FAILURES`, and `PROVIDER_COOLDOWN_SECONDS` are the five config values. All default to unset, which means no pacing and no cooldown, so default behavior stays unchanged.
- Retry behavior: the shared `post_json()` helper owns retry execution and backoff. Call sites supply the operation deadline and attempt count: generation uses `GENERATION_DEADLINE_SECONDS` and `MAX_GENERATION_ATTEMPTS`, while embeddings use `deadline_seconds=60` and the helper's default `max_attempts=3`. The earlier `provider_retry_*` settings were removed as unused.
- Retry-After semantics: wait `max(backoff, Retry-After)`, then bound it by the remaining deadline; `Retry-After` is never required and is ignored when absent or invalid.
- Cooldown accounting: only retryable errors (`rate_limited`, `server_error`, `timeout`) and the deadline `TimeoutError` count toward the cooldown; non-retryable errors do not.
- Half-open behavior: the circuit breaker allows exactly one probe request at a time; a second request is refused until the probe records success or retryable failure.
- Token estimation: tokens-per-minute throttling uses an estimate based on characters divided by four until a real usage-logging token count is available.
- Not done here: usage logging and the usage table for 18a-3, a second provider or fallback route for 18b, and any database change.
- Differences from earlier sections of this note:
  - Scope and Inventory describe a design-only state and direct `post_json()` call path; this implementation exists, and generation plus `scripts/embed_chunks.py` now route through `guarded_post_json()`.
  - Layering proposed separate `generate()`, `embed()`/`embed_many()`, `classify_error()`, and `UsageLogger` interfaces. The adapter exposes guarded `post_json()` only; it uses typed exceptions and internal HTTP classification, and has no usage logger.
  - The earlier claim that graph, scripts, and tests remain unchanged is not true for imports and call routing, although public generation and embedding function signatures remain unchanged.
  - The limiter is process-wide for the Gemini adapter rather than separately keyed per model and operation. Unset limits disable it rather than failing closed when limits are unknown.
  - Usage logging, operation tags, the usage table/report, a gateway, and a second provider remain unimplemented.
  - Retry mechanics remain in the shared `post_json()` helper, while deadlines and attempt counts are supplied by each call site.

## Implementation notes (item 18a-3)

- Code locations: `app/db/models/usage.py` defines `ProviderUsageLog`; `app/providers/usage.py` defines the entries, operation context, and null/database loggers; `app/providers/usage_report.py` contains pure aggregation and formatters; `scripts/usage_report.py` is the read-only CLI.
- Migration: `20261030_0005_provider_usage_log.py` creates `provider_usage_log` with status/error-class checks and indexes.
- Logging is disabled by default through `PROVIDER_USAGE_LOG_ENABLED=false`. When enabled, each logged provider call is persisted in its own short session; logger failures emit only a warning containing the exception class and do not change the provider result or exception.
- The supported operation tags are `query_embedding`, `document_embedding`, `generation`, `experiment_embedding`, and `evaluation`. The active `usage_operation(tag)` context overrides the explicit call-site tag and is reset on context exit.
- `scripts/investigate.py` already creates a UUID correlation ID for each investigation. The provider logger now uses that ID through `correlation_id_var`; direct provider calls outside an investigation context generate a UUID for each usage entry.
- Latency is elapsed adapter time in milliseconds, excluding rate-limiter waiting. `attempt_count` is the number of provider attempts started, updated by `post_json()` on each attempt. Input/output tokens are taken only from integer Gemini `usageMetadata.promptTokenCount` and `candidatesTokenCount` values. Cooldown refusals record zero attempts and no latency.
- No prompt, response, source-code text, API key, or request payload is stored. Non-provider exceptions such as `ValueError` are not logged; classified provider failures, deadline timeouts, and cooldown refusals are logged.
- Differences from earlier sections of this note:
  - The earlier scope, inventory, and usage-log sections describe a design-only state; the model, migration, logger, operation tags, and report are now implemented.
  - The design table described `attempt_count` as retries attempted; implementation records attempts started, including the initial attempt.
  - The earlier report description named provider/model/status aggregation; the report also groups by operation tag and error class and includes attempt totals, latency statistics, and token sums.
  - The earlier migration section named `20261026_0004` as latest and proposed a 0005 migration. Revision `20261030_0005` is now the latest and adds the usage table.
  - The layering section proposed separate generation/embedding interfaces; this implementation keeps the existing Gemini `post_json` adapter and adds a `UsageLogger` protocol rather than introducing those interfaces.
  - Correlation IDs are reused from the investigation flow when available; standalone calls use generated IDs rather than a caller-provided stable trace ID.

## Implementation notes (item 18b)

- `app/providers/groq.py` implements the optional Groq Chat Completions adapter. It owns a separate limiter and cooldown and uses the existing typed provider errors and usage logger.
- `app/investigation/generation.py` tries Gemini first and attempts Groq only when explicitly enabled and fully configured, after a retryable failure or open Gemini cooldown. Auth, bad-request, safety-blocked, and schema-invalid failures do not trigger fallback.
- Groq output is converted to the existing Gemini response envelope and validated through the same parser. The graph and persistence report the selected generation model; embeddings remain Gemini-only.
- All Groq settings default to unset except `GROQ_FALLBACK_ENABLED=false` and `GROQ_TIMEOUT_SECONDS=60`. No database migration or new runtime dependency was needed; existing usage rows already include provider and model.
- See [the Groq fallback note](../notes/13-groq-generation-fallback.md) for verified provider facts, privacy considerations, source URLs, and the manual live check. Groq facts were checked on 2026-10-30; the raw authorization-header spelling and numeric free-plan quotas remain unverified.
