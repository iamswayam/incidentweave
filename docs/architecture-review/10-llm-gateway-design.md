# LLM gateway design (item 18a-1)

## Scope

This note covers the design and call-site inventory for the LiteLLM gateway decision in [09-llm-gateway-decision.md](09-llm-gateway-decision.md). It does not implement the gateway or change application behavior. The working assumption remains that the application, scripts, evaluation harness and tests continue to run without a live provider dependency in CI.

This document is a design-only record. No code, no compose change, no baseline, no gate and no manifest file is modified here.

## Inventory summary

The project makes Gemini provider calls today in four categories:

- generation: grounded answer generation via `app/investigation/generation.py`
- query embedding: `scripts/investigate.py` and `scripts/search_repo.py`
- repository/document embedding: `scripts/embed_chunks.py` and the evaluation embedding cache path
- experiment pacing: `evaluation/chunking_experiment.py` and `scripts/run_chunking_experiment.py` for `--batch-delay-seconds`

The direct call path is centralized in `app/providers/gemini.py`, which enforces the `x-goog-api-key` header and bounded retry logic. Higher layers mostly call it indirectly without custom retry logic. The API layer does not hit the provider directly; it delegates to the investigation script, which ultimately calls into the shared provider helper and the embedding helper.

## Call-site inventory

| Location | Function | Current model / call | Secret or key loading | Retry and error handling | Test replacement | CI / operational note |
|---|---|---|---|---|---|---|
| `app/providers/gemini.py` | `get_gemini_api_key()`, `send_once()`, `post_json()` | Common Gemini HTTP helper for both generation and embedding calls. `post_json()` uses HTTP POST to a provider URL with `x-goog-api-key` header. | Reads `GEMINI_API_KEY` from process environment via `os.getenv()` and raises `RuntimeError` if missing. | Retries on `429`, `500`, `502`, `503`, `504`; uses bounded exponential backoff + jitter; whole-operation timeout with `asyncio.timeout`; on final failure raises `RuntimeError` with the body redacted of the key. Non-retryable HTTP errors are raised immediately. | Unit tests use `httpx.MockTransport` and monkeypatch the environment; they assert the key is in the header and not in the URL. | CI does not require a live key or gateway. These tests are fully mocked and do not call the live Gemini service. |
| `app/investigation/generation.py` | `generate_investigation()` | Model `gemini-3.5-flash-lite`; endpoint `https://generativelanguage.googleapis.com/v1beta/models/gemini-3.5-flash-lite:generateContent` with JSON schema mode. | No direct key handling; calls the shared `post_json()` helper, which loads `GEMINI_API_KEY`. | No additional retry in this function; the provider helper enforces the retry policy (`deadline_seconds=90`, `max_attempts=3`). | Tests replace `make_client()` with a mock transport and assert request payload, header and schema behavior. | No live key or gateway in CI. |
| `app/investigation/graph.py` | `generate()` state node | Calls `generate_investigation()` as part of the LangGraph investigation flow. | Same as above; no direct key reads. | No custom retry; inherits provider retry. | Unit tests monkeypatch `graph_module.generate_investigation` with fake generation functions. | CI tests against graph logic without a provider call. |
| `scripts/embed_chunks.py` | `embed_text()`, `embed_texts()`, `embed_repository_chunks()` | Embedding model `models/gemini-embedding-001`; `outputDimensionality` is fixed to 768; single embedding uses `:embedContent`; batch embedding uses `:batchEmbedContents`. | Uses `post_json()`, which loads `GEMINI_API_KEY` from the process environment. | `embed_repository_chunks()` catches `RuntimeError`, `TimeoutError`, and `ValueError` per batch and records a failed batch count; `embed_text()` and `embed_texts()` raise on unexpected response format or dimension mismatch. | Unit tests monkeypatch environment and mock HTTP responses; they assert the header and exact request body shape for single and batch embeddings. | CI does not call the live provider. |
| `scripts/investigate.py` | `investigate_repository()` | Query embedding call `await embed_text(query_text)` before retrieval and generation; persisted `embedding_model=GEMINI_MODEL` in the replay record. | `GEMINI_MODEL` is a constant; `embed_text()` loads the environment key through the provider helper. | No custom structured retry here. It relies on `post_json()` for provider-level retry/backoff and the outer `asyncio.timeout(INVESTIGATION_DEADLINE_SECONDS)`. Errors are persisted via `persist_error()` when the investigation fails. | Integration tests replace `embed_text` and the graph-level generation calls with stubs. | Evaluation and CI do not depend on a live Gemini key while tests are mocked. |
| `scripts/search_repo.py` | `main()`, `search_repository()` | Query embedding for a repository search; `embed_text(args.query)` followed by hybrid search. | Same as above. | No custom retry; provider helper handles it. | Not generally covered by focused unit tests; CLI tests mock the helper or bypass a provider call. | No live provider dependency in CI. |
| `app/api.py` | `create_investigation()`, `get_investigation()` | API entry point, but not a direct provider call; it delegates to `investigate_repository()`. | No direct key handling. | Converts provider or validation failure into HTTP errors (`502` upstream failure, `422` validation error, `404` repository not found). | API tests assert response schema and error mapping without hitting live Gemini. | CI requires no gateway or provider key. |
| `evaluation/runner.py` | `load_key_without_logging()`, `cached_embedding()`, `_counted_send_once()` | Evaluation-only query embedding cache and generation throttling. Uses the same Gemini embedding and generation calls but with a short evaluation budget and pacing. | Reads `.env` locally only if `GEMINI_API_KEY` is absent; it never logs the secret. | `MIN_API_DELAY_SECONDS = 1.5` is used between provider calls; generation requests are counted and capped by `MAX_GENERATION_HTTP_CALLS`. `429` is counted and the generation budget aborts when exhausted. | Evaluation tests monkeypatch provider behavior and validate the call budget, cache reuse and request throttling. | CI does not require live Gemini access for the regression suite; the offline evaluation uses fixtures and mocks. |
| `evaluation/chunking_experiment.py` | `plan_embeddings()`, `embed_missing()`, `_embed()` | Chunking experiment embed command: batches pending embeddings and writes vectors under `evaluation/cache/chunk_embeddings/`. Uses `scripts.embed_chunks.embed_texts`. | Falls back to `app.config.settings.gemini_api_key` and then reads `.env` if needed; the command requires `GEMINI_API_KEY`. | `embed_missing()` respects `batch_delay_seconds` by sleeping between batches; if later batches are requested, it automatically pauses between them. There is no app-side provider fallback in this command. | Unit tests patch `embed_missing()` and `embed_texts()` to validate cache reuse, ordering and `--batch-delay-seconds` behavior. | This path is an evaluation command, not part of the normal CI path unless intentionally run by maintainers. |
| `scripts/run_chunking_experiment.py` | `_embed()` and CLI parsing | Exposes the `embed` subcommand; it calls `embed_missing(..., batch_delay_seconds=<arg>)` and records the cached embeddings. | Same as above; resolves `GEMINI_API_KEY` from env or settings. | no provider fallback; it fails fast when the key is missing. | Unit tests assert the CLI rejects negative `--batch-delay-seconds` and the pacing logic is applied. | Not part of the default CI run. |
| `evaluation/build_fixture.py` | `build_fixture()` | Stores model metadata including the embedding model used by the fixture (`models/gemini-embedding-001`). | Uses the same model constant; no separate key loading here. | No network calls here; it records schema metadata only. | Tests compare fixture shape and recorded model names. | No live provider network in CI. |
| `tests/unit/test_gemini_provider.py` | `test_post_json_retries_503_with_exponential_jitter()`, etc. | Uses mocked `httpx.MockTransport` to validate retry, backoff and redaction behavior. | Sets `GEMINI_API_KEY` in the environment. | Verifies retries and redaction. | This is the replacement pattern for all provider tests. | CI passes without live provider access. |
| `tests/unit/test_gemini_api_key_header.py` | `test_generate_investigation_sends_key_in_header()` etc. | Mocked provider call assertions for both generation and embeddings. | Sets `GEMINI_API_KEY` in the environment. | Confirms the key is sent in the header and never in the URL. | The accepted test harness for the current provider contract. | CI-safe and fully offline. |
| `tests/unit/test_chunking_experiment.py` | `test_embed_missing_waits_between_batches()` etc. | Validates the chunking experiment pacing contract. | Uses `monkeypatch.setenv` and a fake embed function. | Verifies the configured delay is applied between batches. | This is the official test replacement for pacing logic. | CI-safe; no network dependency. |

Notes:

- There is no direct call to a live provider from the app API or from the normal FastAPI route. The provider is reached through a shared helper and a small number of script entry points.
- There is no current gateway or dashboard integration in the repository. The decision in [09-llm-gateway-decision.md](09-llm-gateway-decision.md) is to replace those direct calls with a single OpenAI-compatible upstream while denying silent direct-provider bypasses.
- The embedding-cache path is intentionally separate from the runtime query path: `evaluation/cache` stores vectors on disk and is used for offline comparisons, while `app` still relies on the live embedding call when a query is embedded at runtime.

## Environment: how the app and Postgres run today

From [docker-compose.yml](../../docker-compose.yml):

- Service `db` runs `pgvector/pgvector:pg17` on `5432:5432`.
- Postgres environment is:
  - `POSTGRES_DB=incidentweave`
  - `POSTGRES_USER=incidentweave`
  - `POSTGRES_PASSWORD=incidentweave`
- Health check: `pg_isready -U incidentweave -d incidentweave` every 5 seconds.
- Service `app` builds from `docker/Dockerfile`, exposes `8000:8000`, and depends on `db` via `service_healthy`.
- The application environment currently sets `APP_ENV=development` and `DATABASE_URL=...db:5432/incidentweave` inside Compose, while the local `.env.example` file uses `DATABASE_URL=localhost:5432/incidentweave` for host-local execution.
- There are no explicit named volumes or init scripts in the current Compose file; the database data is container-local unless Docker adds its own default storage behavior. There is no gateway service or Docker secret configuration yet.

From [.env.example](../../.env.example):

- `APP_ENV=development`
- `DATABASE_URL=localhost:5432/incidentweave`
- `GEMINI_API_KEY=`
- `API_PROTECTION_SECRET=`

This means the current repo expects provider keys to be supplied through the local environment, not committed in the repository. That is consistent with the decision record's requirement to keep config secret-free and keys in ignored local files or Docker secrets.

### Creating a second database for the gateway

The decision record prefers a self-hosted LiteLLM service using its own database in the existing PostgreSQL instance. The design therefore is:

- keep the existing `db` service as the PostgreSQL host
- create a second database, for example `litellm`, inside that same instance
- configure the gateway to use a separate `DATABASE_URL` or connection string pointing to that database
- keep application database credentials and gateway database credentials separate, and do not commit either in version control

This is simpler than a second Compose service unless there is a specific isolation requirement. A second service is possible, but it adds another port mapping and another PostgreSQL image lifecycle to maintain. The simplest operational layout is: same Compose network, same PostgreSQL service, second database in the same cluster, gateway service attached to that network.

### Windows and Docker Desktop notes

The repository is written to run on a local Windows development machine, and the current configuration uses `localhost` for the local app and `db` inside Compose. Two practical constraints apply:

- On Windows with Docker Desktop, the Compose service name `db` resolves on the Docker network but `localhost` resolves to the host OS, not the container network. This is why `DATABASE_URL` differs between host-run and container-run settings.
- The current app is likely run either directly on Windows or inside the app container. In both cases, the runtime must choose the correct target host (`localhost` for the host OS, `db` for Compose-internal services). Never assume `localhost` works from inside the container.
- Docker Desktop on Windows usually runs the engine through WSL2 or the Hyper-V VM backend; the Compose network is still internal to Docker, and the gateway should use the Compose network name rather than the host’s loopback address when it must talk to Postgres.
- Use explicit environment variables for the app and any gateway service rather than hard-coding hostnames. Avoid cross-platform assumptions about Unix sockets and bind mounts.

### Where the gateway service should sit

The gateway should be a sibling service in the same Compose project, alongside `app` and `db`, not an app dependency. The preferred layout is:

- `db` remains the Postgres service for IncidentWeave data
- `gateway` (or `litellm`) is a separate Docker service in the same project network
- the app connects to the gateway over the Compose network with an OpenAI-compatible base URL such as `http://gateway:4000`
- the gateway connects to Postgres on the internal Docker network using the database credentials for the `litellm` database
- the gateway dashboard and usage DB live in the same Compose stack, but the UI is not exposed to the public internet without explicit need

This keeps the application provider interface stable while consolidating retries, quotas and usage tracking in one service.

## Design note

### Client choice

Two patterns are possible:

1. OpenAI-compatible client pointed at the gateway for generation and embeddings
2. Keep provider SDK for some calls and only route a subset through the gateway

The decision record prefers option 1. The gateway is purposely selected to centralize retries, quotas, usage logging and a dashboard. The application should present one OpenAI-compatible interface to the proxy and never silently bypass it. The direct provider client should remain only in tests or in a clearly labeled exceptional script path that is not used by the app runtime.

Recommended operational direction:

- generation: go through the gateway
- query or document embeddings: also go through the gateway if the pinned version supports the required Gemini embedding API semantics
- if the gateway cannot support the exact embedding contract, keep direct embeddings as a temporary exception only with explicit, auditable configuration and no silent fallback

### Config and secrets layout

The repo should remain secret-free. The pattern is:

- commit only `docker-compose.yml`, config templates, and a checked-in `.env.example` that contains blanks or placeholders
- keep actual keys in a local ignored `.env` file or in Docker secrets when running in Docker Compose or deployment
- set the gateway master key and provider keys in the runtime environment only; never print them in logs or logs to the application-facing dashboard
- the app should not store provider secrets in config objects or in the repository; `app/config.py` should only hold non-secret runtime values and read secret values from the environment when needed

The current `.env.example` already has the right structure for `GEMINI_API_KEY` and `API_PROTECTION_SECRET`. The gateway adds more keys and a master key, but the repository should still contain no real secret values.

### Image pinning procedure

Required procedure for the implementation that follows this design note:

1. Use the official LiteLLM Docker image from the official image source and pin it to a version of `1.83.0` or later.
2. Pin the image by digest, not by floating tag.
3. Record the digest, the date it was verified and the exact image reference used in the repo or deployment note.
4. Use the same pinned image in the Compose service definition and keep the digest in the source control record.
5. Verify the image signature process before deployment, using the official signing process documented by the image provider.

This repository has no live network access and no access to the LiteLLM registry documentation in this session. Therefore the exact lookup command for the digest, the exact registry path and the exact signature verification method are not independently verified here. The following are explicitly unverified facts for this design note:

- the exact official image name and registry path for the proxy image
- the exact `docker buildx imagetools inspect` or registry command to resolve the digest
- the exact cosign or signature-verification command sequence
- any claim that the LiteLLM proxy supports a specific Gemini embedding option in the exact pinned version without reading the source or official docs

### Retry ownership

The gateway owns retry behavior. The application must not retry the same failure again after the gateway has already handled it. This is critical because a provider failure is already classified once at the proxy boundary; the app should mostly treat the gateway as a single upstream and fail explicitly if the gateway reports a terminal error.

This means:

- gateway: retry loops, exponential backoff, jitter, `Retry-After` handling when present, cooldowns and per-provider routing
- app: one request to the gateway, no second retry of the same failing call, no silent fallback to a direct provider client
- upstream classification: 429s, timeout, 5xx, bad request, connection failures and explicit rate-limit exhaustion must be surfaced to the app as structured errors the app can log and present

### Pacing

Pacing belongs in the gateway in the same way as retry ownership does. The application should not infer its own provider pacing or use direct provider calls during normal operation. The gateway should apply:

- per-model request pacing
- per-user / per-key pacing
- short cooldowns after rate-limit events
- queueing or per-operation rate caps for embedding and generation traffic

The current code already has evaluation-specific pacing in `evaluation/runner.py` and `evaluation/chunking_experiment.py` via `MIN_API_DELAY_SECONDS` and `--batch-delay-seconds`. Those are tool-side rate-limit controls for offline work, not the runtime contract for the app. The gateway should take ownership of runtime pacing for production and for any repeated automation.

### Error classification mapping

The app should receive a limited, stable set of failure classes instead of raw provider exceptions. A practical mapping is:

| Failure class | Meaning | Expected app behavior |
|---|---|---|
| `rate_limited` | 429 or quota exhaustion | surface a clear upstream failure; do not retry again in app |
| `timeout` | provider or gateway request timed out | mark as timeout and fail explicitly |
| `server_error` | 5xx response from provider or gateway | fail explicitly; gateway can retry internally |
| `bad_request` | invalid model, invalid payload, unsupported parameter | fail and record the request metadata without logging secrets |
| `gateway_unavailable` | gateway itself is down or cannot reach the provider | fail explicitly, never silent fallback to direct provider |
| `invalid_response` | malformed JSON or unexpected schema | fail explicitly and log the classification |

This is not a replacement for the provider helper's retry logic; it is the operational contract between the app and the proxy.

### Usage tags per operation

The gateway should assign tags so that spend and rate usage can be grouped by operation. The design record should keep the following tags explicit:

- `operation=query_embedding`
- `operation=document_embedding`
- `operation=answer_generation`
- `operation=chunking_experiment`
- `operation=offline_evaluation`
- `operation=debug` or `operation=local_dev`

The app can also add a small set of metadata fields:

- `repository` or `repo_id`
- `model`
- `provider`
- `user` or `service`
- `component` such as `api`, `script`, `eval`, `ci`

The exact tag set is not yet implementation-committed; the key requirement is that every operation is identifiable in the gateway UI and logs.

### What is logged

The proxy should record, at minimum:

- request timestamp
- request ID or correlation ID
- operation tag
- model and provider
- response status and classification
- latency and token counts if available
- cost estimate if available
- request keys / user labels in a safe, non-secret form
- whether the request was a retry or a direct call

The app should record its own operational trace, but it should not log provider keys, raw API secrets or the full payload body when it contains code or secrets. The current audit and replay design (items 7–8) remains the app's durable evidence record; the gateway adds provider and cost telemetry rather than replacing the app's own trace.

### Behaviour when the gateway is down

Explicit failure only. The application must not silently fall back to a direct direct-provider call. If the gateway is unreachable or fails a request, then the app must surface an error and stop; it may record the failure in its own trace, but it must never hide a gateway outage by contacting the provider directly.

The design rationale is simple: direct-provider fallback without an explicit rule makes the system inconsistent, bypasses quotas and improves the chances of accidental cost blow-ups or policy violations.

### CI

The design works with CI without requiring any gateway or secret. The test philosophy remains the same as the current code: mock the HTTP layer and keep the provider contract in test doubles.

CI expectations:

- no live gateway service needed
- no live `GEMINI_API_KEY` required
- tests patch the client and assert headers, retry behavior and request schema
- the offline evaluation and embedding cache remain unchanged and deterministic unless the maintainer explicitly runs them with a real key

### Offline evaluation and embedding cache

The design does not change the current offline evaluation behavior or the embedding cache semantics. The current evaluation flow writes cached embeddings under `evaluation/cache` and records the embedding model in metadata. That remains unchanged.

The gateway must not silently alter the semantics of the cached embedding data. If the gateway is in front of embeddings, it must still preserve the same model / dimension contract for the evaluation path. The evaluation harness is intentionally an offline comparison system; it should continue to load by pinned model metadata rather than by a dynamic gateway default.

### Security rules from the decision record

The design adopts the security rules stated in [09-llm-gateway-decision.md](09-llm-gateway-decision.md):

- use the official LiteLLM Docker image
- pin by digest at version `1.83.0` or later
- never `pip install` an unpinned LiteLLM package into the application or CI environment
- commit only secret-free configuration
- store provider keys in ignored local `.env` or Docker secrets, not in the repo
- keep secret values out of logs and dashboard configuration
- verify the image digest and signature process before deployment

## Embeddings question: what is verified and what is not

This item is intentionally conservative because the repository took no live web access and no dependency installation. The project has already recorded the following fact from the decision record:

- the LiteLLM Gemini embedding docs show a `dimensions` parameter in the Python SDK
- a LiteLLM proxy example shows only `model` and `input`
- the decision record states that `task_type` is not mentioned in the proxy example and that the project cannot confirm it from the codebase alone

What we can verify from the repository itself:

- the app currently uses `models/gemini-embedding-001` and `outputDimensionality` = `768` in [scripts/embed_chunks.py](../../scripts/embed_chunks.py)
- the DB schema enforces `Chunk.embedding` to be 768-dimensional in the database model logic, and the tests assert 768 length
- the current app expects an embedding vector of length 768 in query and document embedding paths

What we cannot verify without reading the official LiteLLM docs or the pinned image version itself:

- whether the gateway supports Gemini embedding `task_type` exactly as `RETRIEVAL_DOCUMENT` and `CODE_RETRIEVAL_QUERY` for the pinned version
- whether the proxy accepts the `dimensions` parameter, and whether it forwards or transforms it correctly for Gemini models
- whether the proxy supports `task_type` for the exact model family at the exact version we will pin

This means the exact Gemini embedding contract for the gateway is unverified until the maintainer reads the official docs for the chosen pinned version and confirms the supported parameters in that image.

### Embedding options and trade-offs

Option A: embeddings through the gateway

- Pros: one rate-limit boundary, one usage dashboard, consistent request tagging, no direct embedding API calls from the app
- Cons: exact support for Gemini `task_type` and `dimensions` is unverified for the pinned LiteLLM version; if unsupported, the app may fail or silently use a different default behavior

Option B: generation through the gateway, embeddings remain direct with app-side retry, pacing and usage logging

- Pros: the current direct-embedding path already works and is covered by tests; limited disruption to the production retrieval path; avoids depending on an unverified gateway feature
- Cons: duplicates provider logic and rate control; leaves embeddings outside the gateway dashboard and misses the single upstream operating model

Option C: another route

- Example: use a local open embedding model under the separate 18c protocol while leaving generation behind the gateway, or defer the embedding decision until after a separate validation harness
- Pros: isolates experimental risk and preserves generation routing
- Cons: adds complexity and a second embedding path, which the decision record explicitly warns against because vectors from different embedding models are not interchangeable

Recommendation for the maintainer: do not treat any gateway embedding route as decided without the pinned version check. The conservative design is Option B for the current work if the gateway is not confirmed to support the required Gemini embedding contract; if support is confirmed for the chosen pinned version, Option A becomes the preferred design.

## Decision list for the maintainer

1. Embeddings path (item 14a / 18a)
   - Options: A = gateway embeddings; B = direct embeddings + app-side pacing/retry; C = defer embeddings and use a separate local-model path
   - This is the highest-risk decision because `task_type` and `dimensions` support are still unverified for the pinned LiteLLM version.

2. Client choice
   - Options: use an OpenAI-compatible client everywhere through the gateway; keep the Google SDK only for exception paths; or keep direct embeddings on the current path while routing generation through the gateway
   - Recommended default: keep the app on one OpenAI-compatible client for generation and embeddings if the gateway supports the required contract; otherwise, keep direct embeddings only as an explicit and temporary exception.

3. Usage data and dashboard location
   - Options: LiteLLM usage database in the same Postgres instance; a separate Postgres database service; or self-hosted dashboard outside the app stack
   - Recommended default: LiteLLM database in the same PostgreSQL service, with the gateway and dashboard as a sibling service in the Compose stack.

4. First Gemini generation model
   - Options: current `gemini-3.5-flash-lite`, a newer Gemini model, or an ordered fallback scheme that starts with a cheaper model
   - Recommended default: keep the current model initially for stability, then allow the gateway to move to a fallback order later under item 18b.

5. Gateway master-key handling for local use
   - Options: local `.env` only; Docker secrets only; or both
   - Recommended default: local ignored `.env` file for development and Docker secrets for deployment, without storing the actual values in the repository.

## Checklist split for item 18a

The original item 18a commitment is now split into two stages:

### 18a-1. Design and inventory
- *Fix:* inventory every provider call path and write the gateway design for routing, retries, pacing, secrets, dashboard placement and failure semantics.
- *Done when:* the call inventory and design note are committed, cross-references are updated, and the maintainer has a decision list for the remaining implementation choices.
- **Status:** In progress; PR pending.

### 18a-2. Implement the approved gateway foundation
- *Fix:* implement the LiteLLM sidecar, use the gateway for generation and embeddings only after the design decision is confirmed, pin the image by digest, commit secret-free config, and wire the application to use the gateway with the documented retry, pacing and telemetry behavior.
- *Done when:* Compose service and secret-free config are committed; the app calls the gateway for generation and document/query embeddings; app usage is visible in the dashboard; embeddings have no cross-model fallback; unit tests mock the gateway; CI requires neither gateway nor key; offline evaluation and embedding cache are unchanged; security rules are documented; and the existing terminal trace plus the promised per-stage telemetry are covered.
- **Status:** Not started; PR pending.

## Progress log entry for the design note

The design work for 18a-1 is intentionally documentation-only and does not implement any runtime change. The implementation work for 18a-2 is explicitly not started.
