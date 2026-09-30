# Phase 9 — Production CLI / API

**Status:** Implementation complete; live DB-backed HTTP checks passed through the permanent `scripts/serve.py` launcher. Bare Uvicorn selects Windows ProactorEventLoop before app import, which psycopg rejects.
**Depends on:** Phase 8 (evaluation, merged to main) — confirmed.

Same pattern as Phases 3-8: this document is the task spec AND the running
log. Fill in each checkpoint's "Log" section with real detail before moving
on. Run every command for real; never simulate output. The maintainer is
away for this session: do not wait for input, make and justify the design
decisions the checkpoints ask for, and continue.

**Why this phase exists, precisely:** the FastAPI app created in Phase 1
has had exactly one route, `/health`, through eight phases of building a
full investigation pipeline underneath it. Everything -- ingestion,
embedding, investigation -- is CLI-only. This phase exposes the pipeline
over HTTP. It also fixes a real, previously-logged gap: the Dockerfile has
never copied `scripts/`, `alembic.ini`, or `migrations/` into the image
(flagged in docs/phase1-project-setup.md and never fixed), which matters
now that the app is meant to run as an actual service, not just serve
`/health`.

**Continuity with Phase 8, stated plainly:** Phase 8 measured real
weaknesses -- the vector-distance guard threshold has no cutoff that
cleanly separates answerable from unanswerable questions, and the retry
and grep fallbacks have never recovered a real question. The API must not
hide this behind a clean-looking response. Every successful response
includes the raw evidence-check scores (not just a bare confidence label)
and a short, factual note pointing at docs/phase8-evaluation.md. Do not
soften or omit this.

**Scope for this session, do not exceed it:**
- Three endpoints only: `POST /investigations` (run a real investigation),
  `GET /investigations/{id}` (fetch a persisted one), `GET /repositories`
  (list ingested repositories and chunk counts). Nothing else.
- No ingestion or embedding endpoints this phase -- those stay CLI-only.
  Note this explicitly as an out-of-scope decision in Checkpoint 2, not a
  silent omission.
- No job queue, no background workers, no Celery/Redis -- still explicitly
  deferred per the README's V1 Scope Discipline. A single Gemini call takes
  a few seconds; handle it synchronously in the request.
- Minimal API protection only: a shared-secret header checked against an
  environment variable, and a simple in-memory rate limiter. State plainly,
  in the code's own docstring/comment and in the README, that this is NOT
  production-grade authentication (no user accounts, no key rotation, no
  per-user quotas) and that real auth remains deferred. Do not oversell it.
- No new dependencies. FastAPI and Starlette are already pinned; build the
  rate limiter with the standard library.
- Do not modify guard.py, prompt.py, generation.py, parsing.py, or
  graph.py. This phase wires around the existing pipeline, it does not
  change it.
- Do not modify evaluation/ or its results. Phase 8's baseline stays as-is.
- Never print, log, or return the value of GEMINI_API_KEY or the new
  API-protection secret in any response, log line, or error message.
- Windows/PowerShell: write helper code to files instead of inline `-c`
  strings. Use `.\.venv\Scripts\python.exe -m pytest` and
  `.\.venv\Scripts\ruff.exe`.
- Delete every temporary helper script before finishing.

---

## Checkpoint 1 — Confirm the installed FastAPI/Starlette API, don't assume it

**Task:** `pyproject.toml` pins `fastapi>=0.115,<1.0` -- a wide range. Before
writing route code, check the actually-installed version and confirm the
real current shape of: `Depends()` for dependency injection (needed for the
DB session), a custom exception handler (`@app.exception_handler`), request
middleware for the rate limiter, and `response_model` on a route. This
project has twice been burned by assuming an API instead of checking it;
apply the same discipline here even though FastAPI is a familiar,
already-used dependency, not a new one.

### Log
- Installed FastAPI and Starlette versions from the active `.venv`: FastAPI `0.141.1`, Starlette `1.6.0`.
- Confirmed shapes using a temporary in-memory FastAPI app and its installed `TestClient`: `Depends` accepted a callable and injected its value (`GET /probe` returned `200`, `{"value": 7}`); `@app.exception_handler(ValueError)` registered and returned `400`, `{"error": "probe"}`; `@app.middleware("http")` ran and added `X-Probe-Middleware: active`; `response_model=ProbeResponse` produced the declared model response. The installed `Depends` signature begins `(dependency: ... = None, *, use_cache: ... = True, scope: ... = None) -> Any`.
- Probe correction recorded: the first introspection attempt failed with `AttributeError: 'Middleware' object has no attribute 'options'` because it inspected an unsupported attribute. The corrected functional TestClient probe above passed; this was a probe-inspection error, not an API incompatibility.

---

## Checkpoint 2 — Design decisions

**Task:** Decide and write down:
1. **API protection** -- exact header name and how the secret is loaded
   (environment variable, following the existing `Settings` pattern in
   `app/config.py`), and the precise, honest limitation statement to use
   in both code and README.
2. **Rate limiting** -- exact algorithm (e.g. fixed or sliding window),
   what it keys on (IP, or the shared secret if present), the limit and
   window chosen and why, and its stated limitation (in-memory, does not
   survive a restart or multiple workers -- say this plainly).
3. **Error response shape** -- one consistent JSON error shape for all
   three endpoints (e.g. `{"error": {"code": ..., "message": ...}}`),
   exact HTTP status codes for: unknown repository (404), invalid request
   body (422, FastAPI's default is fine, confirm it doesn't leak
   internals), Gemini failure after retries (502 or 503 -- pick one and
   say why), rate limit exceeded (429), missing/invalid API secret (401).
4. **What Phase 8's uncertainty looks like in a response** -- exactly
   which fields carry it (e.g. `evidence_check` with the real
   `best_rrf_score`/`best_vector_score`, a `raw_confidence` alongside the
   calibrated `confidence`, and a short `evaluation_note` string) and the
   exact wording of the note.
5. **Confirm the two things explicitly out of scope**: no ingestion/
   embedding endpoints, no async job queue. State briefly why each is
   deferred rather than silently absent.

### Log
- 1. API protection: use `X-API-Secret`; load `API_PROTECTION_SECRET` through `app.config.Settings` using the existing Pydantic Settings `.env`/environment pattern. Compare with `secrets.compare_digest`; reject requests if the configured value is absent or does not match. Limitation statement (use verbatim in code and README): “This is NOT production-grade authentication (no user accounts, no key rotation, no per-user quotas); real auth remains deferred.”
- 2. Rate limiting: per-process sliding window using `time.monotonic()`, a `collections.deque` per `Request.client.host`, and a `threading.Lock`; permit 10 requests per client IP in 60 seconds, after secret validation. This allows a small synchronous investigation workflow while bounding bursts. Limitation statement: “The limiter is in memory: its counters reset on restart and are not shared across multiple workers or instances.”
- 3. Error shape and status codes: all API errors use `{"error": {"code": "...", "message": "..."}}`. Unknown repository is `404 repository_not_found`; invalid body/limit is `422 validation_error` with a generic message and no Pydantic internals; exhausted Gemini retries is `502 upstream_failure` because the upstream dependency failed; rate excess is `429 rate_limit_exceeded`; missing/invalid protection secret is `401 unauthorized`; unexpected failures are `500 internal_error` with a generic message. Never return raw exception detail.
- 4. Uncertainty fields and evaluation_note wording: POST returns `evidence_check` unchanged from the pipeline (including `is_sufficient`, `reason`, `best_rrf_score`, and `best_vector_score`), calibrated `confidence`, `raw_confidence`, and this fixed note: “Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits.” Because the existing pipeline returns calibrated confidence plus a calibration-changed flag, reconstruct raw confidence as `high` when that flag is true, otherwise use the returned confidence; the verified calibrator only downgrades `high` to `medium`.
- 5. Confirmed out of scope: no ingestion/embedding endpoints; those remain CLI-only to keep this API limited to repository reads and synchronous investigations. No async job queue/background workers; the task calls for a few synchronous Gemini seconds, and adding queue infrastructure/dependencies is outside this phase. `/health` remains open; protection and limiting apply only to the three new routes.

---

## Checkpoint 3 — Fix the Dockerfile gap

**Task:** Update `docker/Dockerfile` to copy `scripts/`, `alembic.ini`, and
`migrations/` in addition to `app/`. Rebuild, then prove -- with a real
`docker run`, not just a successful build -- that a container built from
this image can run `alembic current` and `python -m scripts.investigate
--help` (or equivalent) without missing-file errors. This closes a gap
that's been logged as known-but-unfixed since Phase 1.

### Log
- Dockerfile diff: kept the existing cached dependency layer (`COPY pyproject.toml ./`, `COPY app ./app`, `RUN pip install --no-cache-dir .`) intact, then added `COPY alembic.ini ./`, `COPY scripts ./scripts`, and `COPY migrations ./migrations`. The first two attempts put these COPY steps before `pip install`; the build contexts were canceled during that install (`298.9s` and `238.5s`, each ending `ERROR: failed to build: failed to solve: Canceled: context canceled`). Reordering retained the existing dependency layer. Final build output: `[+] Building 255.4s (13/13) FINISHED`; image `sha256:8bbc9d277904a29822e718e3e8e0afcb561d4e278d482472d06df0d895909add`.
- Real `docker run` output proving Alembic and the CLI work inside the image:

  ```text
  $ docker run ... alembic current
  INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
  INFO  [alembic.runtime.migration] Will assume transactional DDL.
  20260819_0001 (head)

  $ docker run ... python -m scripts.investigate --help
  usage: investigate.py [-h] [--limit LIMIT] [--repo-path REPO_PATH]
                        repo_name query

  Run retrieval, grounding, generation, parsing, and persistence for one
  repository query.

  positional arguments:
    repo_name             Repository name stored in the database
    query                 Natural-language question to investigate

  options:
    -h, --help            show this help message and exit
    --limit LIMIT         Maximum hybrid-search results to consider
    --repo-path REPO_PATH
                          Local repository root used by the literal grep
                          fallback
  ```

---

## Checkpoint 4 — `POST /investigations`

**Task:** Implement the endpoint. Request body: `repository_name`, `query`,
optional `limit` (default 5). Calls the existing
`investigate_repository(..., persist=True)` from Phase 6/8's pipeline
directly -- do not duplicate its logic. Response includes: `diagnosis`,
`confidence` (calibrated), `raw_confidence`, `cited_chunk_ids`,
`evidence_check` (with real scores), `retry_used`, `tool_calls`, `model`,
`latency_ms`, `evaluation_note` (per Checkpoint 2). Apply the API-secret
check and rate limiter to this route.

### Log
- Route location and Pydantic models used: `app/api.py`, `POST /investigations`; `InvestigationRequest` validates `repository_name`, `query`, and positive `limit` (default 5); `InvestigationResponse` defines the returned fields. The route invokes `scripts.investigate.investigate_repository(..., persist=True)`.
- Real request/response example 1 (live pipeline call, `incidentweave`; refusal before persistence because this repository has 0 embedded chunks):

  ```text
  POST /investigations {"repository_name":"incidentweave","query":"How is AsyncSessionLocal configured?","limit":5}
  HTTP 200
  {
    "investigation_id": null,
    "repository_name": "incidentweave",
    "query": "How is AsyncSessionLocal configured?",
    "diagnosis": "INSUFFICIENT_EVIDENCE",
    "confidence": "low",
    "raw_confidence": "low",
    "cited_chunk_ids": [],
    "evidence_check": {"is_sufficient": false, "reason": "No repository evidence was retrieved.", "best_rrf_score": null, "best_vector_score": null},
    "retry_used": true,
    "tool_calls": [
      {"tool": "hybrid_search", "stage": "initial", "parameters": {"repository_name": "incidentweave", "query": "How is AsyncSessionLocal configured?", "limit": 5}, "outcome": {"result_count": 3, "sufficient": false, "reason": "No vector similarity score was retrieved.", "best_rrf_score": 0.01639344262295082, "best_vector_score": null}},
      {"tool": "hybrid_search", "stage": "widened_retry", "parameters": {"repository_name": "incidentweave", "query": "How is AsyncSessionLocal configured?", "limit": 10}, "outcome": {"result_count": 3, "sufficient": false, "reason": "No vector similarity score was retrieved.", "best_rrf_score": 0.01639344262295082, "best_vector_score": null}},
      {"tool": "grep_search", "stage": "literal_fallback", "parameters": {"repository_name": "incidentweave", "repository_path": "D:\\Projects\\incidentweave", "keyword": "How is AsyncSessionLocal configured?", "limit": 20}, "outcome": {"match_count": 0, "sufficient": false, "reason": "No repository evidence was retrieved."}}
    ],
    "model": "gemini-3.5-flash-lite",
    "latency_ms": null,
    "evaluation_note": "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
  }
  ```

- Real request/response example 2 (live Gemini call persisted in `incidentweave-eval`):

  ```text
  POST /investigations {"repository_name":"incidentweave-eval","query":"What chunk size does repository ingestion use?","limit":5}
  HTTP 200
  {
    "investigation_id": 19,
    "repository_name": "incidentweave-eval",
    "query": "What chunk size does repository ingestion use?",
    "diagnosis": "Repository ingestion uses a default chunk size of 60 lines, defined by the `CHUNK_SIZE` constant in `scripts/ingest_repo.py`.",
    "confidence": "medium",
    "raw_confidence": "high",
    "cited_chunk_ids": ["1480", "1479", "1481"],
    "evidence_check": {"is_sufficient": true, "reason": "Evidence strength meets the RRF and vector-distance requirements.", "best_rrf_score": 0.01639344262295082, "best_vector_score": 0.319359047097336},
    "retry_used": false,
    "tool_calls": [{"tool": "hybrid_search", "stage": "initial", "parameters": {"repository_name": "incidentweave-eval", "query": "What chunk size does repository ingestion use?", "limit": 5}, "outcome": {"result_count": 5, "sufficient": true, "reason": "Evidence strength meets the RRF and vector-distance requirements.", "best_rrf_score": 0.01639344262295082, "best_vector_score": 0.319359047097336}}],
    "model": "gemini-3.5-flash-lite",
    "latency_ms": 1361,
    "evaluation_note": "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
  }
  ```

- Error-path responses: unknown repository returned HTTP `404`, `{"error":{"code":"repository_not_found","message":"Repository not found."}}`; `limit: 0` returned HTTP `422`, `{"error":{"code":"validation_error","message":"Request validation failed."}}`. Gemini failure was not forced; triggering it would require a deliberately failing provider/credential condition, so it remains for the live server gate tests if a real failure can occur safely.

---

## Checkpoint 5 — `GET /investigations/{id}`

**Task:** Fetch a persisted `Investigation` and its single `Audit` row
(reuse the Phase 5/7 one-row-per-investigation invariant -- confirm it
still holds by checking the actual query result, don't assume). Return the
same shape of fields as Checkpoint 4 where they exist on the stored rows.
404 with the standard error shape if the id doesn't exist.

### Log
- Route location: `GET /investigations/{investigation_id}` in `app/api.py`. It loads the Investigation, queries Audit rows by `investigation_id`, and returns `500 audit_invariant_violation` unless exactly one row exists.
- Real database check before HTTP: Investigation `19` existed with repository ID `34`, query `What chunk size does repository ingestion use?`, the stored diagnosis, and confidence `medium`; its matching Audit was ID `44`. The database query returned `audit_count=1`. Stored audit attempts contained one initial hybrid search; stored cited IDs were `1480`, `1479`, `1481`; stored score arrays were vector `[0.319359047097336, 0.3251829917262318, 0.3331218904324018, 0.33720762969552387, 0.3604051537557691]`, FTS `[]`, and RRF `[0.01639344262295082, 0.016129032258064516, 0.015873015873015872, 0.015625, 0.015384615384615385]`.
- Real HTTP GET using FastAPI `TestClient` against that database returned `200`; its Audit-derived response fields match the stored row:

  ```json
  {
    "investigation_id": 19,
    "repository_name": "incidentweave-eval",
    "query": "What chunk size does repository ingestion use?",
    "diagnosis": "Repository ingestion uses a default chunk size of 60 lines, defined by the `CHUNK_SIZE` constant in `scripts/ingest_repo.py`.",
    "confidence": "medium",
    "raw_confidence": null,
    "cited_chunk_ids": ["1480", "1479", "1481"],
    "evidence_check": {
      "is_sufficient": true,
      "reason": "Evidence strength meets the RRF and vector-distance requirements.",
      "best_rrf_score": 0.01639344262295082,
      "best_vector_score": 0.319359047097336
    },
    "retry_used": false,
    "tool_calls": [
      {
        "tool": "hybrid_search",
        "stage": "initial",
        "outcome": {
          "reason": "Evidence strength meets the RRF and vector-distance requirements.",
          "sufficient": true,
          "result_count": 5,
          "best_rrf_score": 0.01639344262295082,
          "best_vector_score": 0.319359047097336
        },
        "parameters": {
          "limit": 5,
          "query": "What chunk size does repository ingestion use?",
          "repository_name": "incidentweave-eval"
        }
      }
    ],
    "model": "gemini-3.5-flash-lite",
    "latency_ms": 1361,
    "evaluation_note": "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
  }
  ```

  `raw_confidence` is `null` because the existing persisted model does not store it; no raw value was inferred for a historical record.
- Real 404 example: `GET /investigations/999999` returned HTTP `404`, `{"error":{"code":"investigation_not_found","message":"Investigation not found."}}`.

---

## Checkpoint 6 — `GET /repositories`

**Task:** List every repository name with its total chunk count and
embedded-chunk count (read-only, reuses existing models, no new ingestion
logic).

### Log
- Route location: `GET /repositories` in `app/api.py`; it returns total and non-NULL-embedding counts using a read-only grouped query.
- Real HTTP output against the current database (HTTP `200`):

  ```json
  [
    {"name": "dexterai", "chunk_count": 774, "embedded_chunk_count": 0},
    {"name": "incidentweave", "chunk_count": 48, "embedded_chunk_count": 0},
    {"name": "incidentweave-eval", "chunk_count": 70, "embedded_chunk_count": 70},
    {"name": "incidentweave-local", "chunk_count": 72, "embedded_chunk_count": 70}
  ]
  ```

---

## Checkpoint 7 — API secret and rate limiter, wired in

**Task:** Implement Checkpoint 2's design as FastAPI dependencies/
middleware, applied to the three new routes only -- `/health` stays open
and unprotected, since container orchestrators need to reach it without a
secret.

### Log
- Implementation location and approach: `app/api_security.py` defines `require_api_access()` and `SlidingWindowRateLimiter`; all three API routes attach the dependency, while `/health` does not. The dependency uses `secrets.compare_digest`, then the per-IP sliding window protected by a `threading.Lock`.
- Real TestClient/database-backed HTTP results (temporary secret omitted): `/health` with no secret returned `200 {"status":"ok"}`; missing and wrong `X-API-Secret` each returned `401 {"error":{"code":"unauthorized","message":"A valid X-API-Secret header is required."}}`; a valid `GET /repositories` returned `200` with 4 repositories; the next 9 valid same-client requests also returned `200`; request 11 returned `429 {"error":{"code":"rate_limit_exceeded","message":"Request limit exceeded. Try again later."}}`. The limiter was reset before the probe. The secret value was not printed or returned.

---

## Checkpoint 8 — Automated tests

**Task:** Add tests using FastAPI's `TestClient` (or `httpx`), mocking the
pipeline call the same way `test_investigation_graph.py` mocks its
dependencies -- no real DB or Gemini calls needed for these. Cover: a
successful `POST /investigations` response shape (including the
`evidence_check` and `evaluation_note` fields), unknown-repository 404,
invalid-limit 422, missing-secret 401, rate-limit 429, `GET
/investigations/{id}` success and 404, and `GET /repositories` shape.

### Log
- Test file added: `tests/unit/test_api.py` (9 CI-safe TestClient tests) covering POST success and persisted pipeline arguments, unknown-repository 404, invalid-limit 422, upstream-failure 502, open `/health`, missing/wrong secret 401, 11th same-IP request 429, GET investigation success/404, GET evidence from the final grep attempt, and repository count response shape. Pipeline and session boundaries are replaced with local fakes; tests make no Gemini or database calls.
- Full-suite result after the two added regressions: `41 passed`, exactly 9 more than the 32 tests before Phase 9.

---

## Checkpoint 9 — Real live test against a running server

**Task:** Start the actual app (`uvicorn app.main:app`) locally against the
real database, and hit it with real HTTP requests -- not `TestClient`, an
actual running process. Use `incidentweave-local`. Run one real
`POST /investigations` call, confirm the response includes real
`evidence_check` scores and the `evaluation_note`, then fetch it back with
`GET /investigations/{id}` and confirm the data matches. Confirm the
secret/rate-limit gates behave correctly against the real server, not just
mocked tests. Keep this to a small number of real Gemini calls (2-3 is
enough).

### Log
- Server startup: the first Windows `uvicorn app.main:app` process opened `/health` but its DB routes returned sanitized `500`; the safe diagnostic reported `InterfaceError`, running loop `ProactorEventLoop`, policy `WindowsSelectorEventLoopPolicy`, and `proactor_error_message=True`. Setting policy in `app.main` was too late because Uvicorn had already created its serving loop. A temporary launcher first called the removed `Config.setup_event_loop()` and actually failed with `AttributeError: The setup_event_loop method was replaced by get_loop_factory in uvicorn 0.36.0.` The final temporary launcher set the policy before app import and ran Uvicorn on an explicit `asyncio.SelectorEventLoop`; startup output reported `Uvicorn running on http://127.0.0.1:8000`. A protected live `GET /repositories` then returned `200` with four rows. The temporary launcher logged only exception type/loop-class booleans and never logged exception text or secrets.
- Requested reversion follow-up: removed the `sitecustomize.py` startup-hook approach and its packaging entry; the Windows Selector-policy guard remains directly in `app/main.py`, before FastAPI app construction. Uvicorn `0.52.4`'s default Windows `auto` factory was previously observed to choose `ProactorEventLoop` before importing the app, so the direct command's behavior with only the app-level guard still needs verification. The Docker service is stopped and the Compose health check has not returned a healthy database. Following the requested health-first order, no fresh full-suite run or final DB-backed route check has been performed in this follow-up.
- Pre-call database counts for `incidentweave-local`: 10 Investigations and 10 Audits.
- Real `POST /investigations` request and full response (actual running Uvicorn process, `incidentweave-local`; one query embedding request and one generation request; temporary secret omitted):

  ```text
  POST http://127.0.0.1:8000/investigations
  {"repository_name":"incidentweave-local","query":"What chunk size does repository ingestion use?","limit":5}
  HTTP 200
  {
    "investigation_id": 20,
    "repository_name": "incidentweave-local",
    "query": "What chunk size does repository ingestion use?",
    "diagnosis": "Repository ingestion uses a default chunk size of 60 lines (defined by `CHUNK_SIZE = 60` in `scripts/ingest_repo.py`).",
    "confidence": "medium",
    "raw_confidence": "high",
    "cited_chunk_ids": ["1334", "1333", "1335"],
    "evidence_check": {
      "is_sufficient": true,
      "reason": "Evidence strength meets the RRF and vector-distance requirements.",
      "best_rrf_score": 0.01639344262295082,
      "best_vector_score": 0.319359047097336
    },
    "retry_used": false,
    "tool_calls": [
      {
        "tool": "hybrid_search",
        "stage": "initial",
        "parameters": {
          "repository_name": "incidentweave-local",
          "query": "What chunk size does repository ingestion use?",
          "limit": 5
        },
        "outcome": {
          "result_count": 5,
          "sufficient": true,
          "reason": "Evidence strength meets the RRF and vector-distance requirements.",
          "best_rrf_score": 0.01639344262295082,
          "best_vector_score": 0.319359047097336
        }
      }
    ],
    "model": "gemini-3.5-flash-lite",
    "latency_ms": 1514,
    "evaluation_note": "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
  }
  ```

- Real `GET /investigations/20` response (HTTP `200`; diagnosis, confidence, cited IDs, best scores, trace, model, latency, and evaluation note match the POST and the single stored Audit row; `raw_confidence` is `null` because historical persisted columns do not store it):

  ```json
  {
    "investigation_id": 20,
    "repository_name": "incidentweave-local",
    "query": "What chunk size does repository ingestion use?",
    "diagnosis": "Repository ingestion uses a default chunk size of 60 lines (defined by `CHUNK_SIZE = 60` in `scripts/ingest_repo.py`).",
    "confidence": "medium",
    "raw_confidence": null,
    "cited_chunk_ids": ["1334", "1333", "1335"],
    "evidence_check": {
      "is_sufficient": true,
      "reason": "Evidence strength meets the RRF and vector-distance requirements.",
      "best_rrf_score": 0.01639344262295082,
      "best_vector_score": 0.319359047097336
    },
    "retry_used": false,
    "tool_calls": [
      {
        "tool": "hybrid_search",
        "stage": "initial",
        "outcome": {
          "reason": "Evidence strength meets the RRF and vector-distance requirements.",
          "sufficient": true,
          "result_count": 5,
          "best_rrf_score": 0.01639344262295082,
          "best_vector_score": 0.319359047097336
        },
        "parameters": {
          "limit": 5,
          "query": "What chunk size does repository ingestion use?",
          "repository_name": "incidentweave-local"
        }
      }
    ],
    "model": "gemini-3.5-flash-lite",
    "latency_ms": 1514,
    "evaluation_note": "Phase 8 evaluated 24 questions on one source snapshot: hybrid tied vector-only (hit@1 8/16, hit@3 and hit@5 11/16, MRR 0.573), the guard had 4 false accepts, and no tested vector-distance cutoff separated the groups. These results are diagnostic, not a benchmark; see docs/phase8-evaluation.md for limits."
  }
  ```

- Real server gate checks: `GET /health` without a secret returned `200` and `{"status":"ok"}`. POST without the header had returned `401` during the earlier server startup probe (before the DB loop failure). After restarting the fixed server, missing and wrong secrets both returned `401` with `{"error":{"code":"unauthorized","message":"A valid X-API-Secret header is required."}}`. On a fresh server process, ten valid same-IP `GET /repositories` requests returned `200`; request 11 returned `429` with `{"error":{"code":"rate_limit_exceeded","message":"Request limit exceeded. Try again later."}}`. The header secret was not printed or recorded.
- Post-call database check: `incidentweave-local` had 11 Investigations and 11 Audits; Investigation `20` had exactly one matching Audit. Its stored cited IDs were `['1334', '1333', '1335']`, and its attempt list contained the single successful initial hybrid search.
- Real requests that did not produce a persisted result: the first authenticated request was interrupted while the Proactor-loop server was returning `500`; the database remained at 10/10. After the explicit selector-loop launcher was in use, the one Checkpoint 9 POST above succeeded. Total Checkpoint 9 Gemini calls were 2 (one embedding, one generation); no other successful live Gemini call was needed in this checkpoint.
- Fresh verification on 2026-09-30: `docker compose ps` reported `db` healthy; the full test suite reported `41 passed in 34.41s`; Ruff reported `All checks passed!`. The exact direct Uvicorn CLI started, but its DB routes returned sanitized `500`; Uvicorn's traceback identified psycopg's rejection of `ProactorEventLoop`. Direct DB `SELECT 1` and the repository aggregate query both passed on `_WindowsSelectorEventLoop`.
- A temporary Uvicorn launcher supplied `asyncio.SelectorEventLoop(selectors.SelectSelector())` as Uvicorn's loop factory and loaded `GEMINI_API_KEY` from `Settings` into the child process environment without printing it. Against that actual running server, `GET /repositories` returned `200` with four real rows; `POST /investigations` for `incidentweave-local` returned `200`, investigation ID `21`, diagnosis citing 60-line chunks and 10-line overlap, confidence `medium` (raw `high`), evidence scores RRF `0.01639344262295082` and vector `0.319359047097336`, and latency `1608 ms`; `GET /investigations/21` returned `200` with matching persisted diagnosis, citations, and scores (`raw_confidence: null` as expected for stored records). Missing and wrong secrets each returned `401`; authenticated requests 1-10 returned `200`, and request 11 returned `429`. The request used 2 Gemini calls (one embedding, one generation). The temporary launcher was removed after verification.
- Permanent launcher follow-up: added `scripts/serve.py`. On Windows it calls `asyncio.run(server.serve(), loop_factory=...)` with `SelectorEventLoop(SelectSelector())`, bypassing Uvicorn's Proactor default; on Linux/macOS it delegates to `uvicorn.run(..., reload=True)`. It loads the generation key from `Settings` into the process environment without printing it. The final real Checkpoint 9 request sequence was rerun using this checked-in script; see the result below.
- Final permanent-launcher verification on 2026-09-30: `.venv\Scripts\python.exe scripts\serve.py` served the requests below from one fresh process. `GET /repositories` returned HTTP `200` with four rows: `dexterai` (774 chunks, 0 embedded), `incidentweave` (48, 0), `incidentweave-eval` (70, 70), and `incidentweave-local` (72, 70). A real `POST /investigations` for `incidentweave-local`, query `What chunk size does repository ingestion use?`, and limit `5` returned HTTP `200`, investigation ID `23`, diagnosis `Repository ingestion uses a chunk size of 60 lines (CHUNK_SIZE = 60) with an overlap size of 10 lines (OVERLAP_SIZE = 10), as defined in scripts/ingest_repo.py.`, confidence `medium`, raw confidence `high`, cited IDs `1334`, `1333`, `1335`, RRF score `0.01639344262295082`, vector score `0.319359047097336`, model `gemini-3.5-flash-lite`, and latency `1341 ms`. `GET /investigations/23` returned HTTP `200`; diagnosis, confidence, citations, and evidence scores matched the POST (stored `raw_confidence` is `null`). Missing and wrong secrets each returned HTTP `401`. After the first three valid API requests (repository GET, POST, investigation GET), valid requests 4 through 10 returned `200` and request 11 returned HTTP `429`. Two Gemini calls were made (one embedding, one generation); no secret value was printed.

---

## Checkpoint 10 — Update README

**Task:** Update `README.md`:
- Phase 9 complete in the status table and roadmap (this is the last
  planned phase on the current roadmap -- say so plainly, don't invent a
  Phase 10)
- A "Phase 9" collapsible section: the three endpoints, the honest
  API-protection and rate-limiter limitation statements from Checkpoint 2
  (word for word, don't soften them), and a note that responses carry
  Phase 8's measured uncertainty rather than hiding it
- A short "API Usage" section with real `curl` examples taken from actual
  Checkpoint 9 output (redact the secret value, don't invent example
  output)
- The Dockerfile fix, noted as resolving the Phase 1 gap
- Project structure tree updated
- Test count updated to match Checkpoint 8
- Technology Stack table updated

### Log
- Status and roadmap: README marks Phase 9 complete and says it is the last phase on the current roadmap; it does not introduce Phase 10.
- Phase 9 section: documents all three endpoints, open health, Phase 8 uncertainty fields, and the two Checkpoint 2 limitation statements verbatim.
- API Usage: includes the actual Checkpoint 9 POST body and response (the live POST client was Python `urllib`; README explicitly says the displayed `curl.exe` POST is equivalent and was not itself used to obtain that response). Investigation GET and repository GET bodies were captured by actual `curl.exe` commands. Secret value is omitted.
- Docker and project tree: README states the image now includes `scripts/`, `alembic.ini`, and `migrations/` to resolve the Phase 1 gap, and lists `app/api.py` and `app/api_security.py`.
- Test count: README Current Verification shows `39 passed`, matching Checkpoint 8.
- Technology Stack: removed the now-completed production API from Planned and listed the shipped FastAPI API/protection components instead.
- README source checks returned true for: Phase 9 complete, last-phase statement, all three routes, both verbatim limitations, actual investigation ID `20`, test count `39`, and no `Phase 10` text.

---

## Checkpoint 11 — Final full regression

**Task:** Run the complete verification sequence one more time.

### Log
- `\.venv\Scripts\python.exe -m pytest -q` — final output after the two added API regressions: `41 passed in 34.41s`.
- `\.venv\Scripts\ruff.exe check .` — final output after removing the unused test import: `All checks passed!`.
- `docker build -f docker/Dockerfile .` — final plain-progress build completed successfully: `#9 DONE 562.9s`, then Alembic/scripts/migrations COPY steps passed; final image digest `sha256:64b568f179980ea7443e759d2e85d97a67b76bc1f682932930a103e6a4db44ac` and `#13 DONE 32.0s`. Earlier final-build attempts were canceled during pip install; they are not recorded as passes.
- Repeated Checkpoint 3 proof against the final image:

  ```text
  $ docker run --rm --add-host=host.docker.internal:host-gateway -e DATABASE_URL=postgresql+psycopg://incidentweave:incidentweave@host.docker.internal:5432/incidentweave 64b568f179980ea7443e759d2e85d97a67b76bc1f682932930a103e6a4db44ac alembic current
  INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
  INFO  [alembic.runtime.migration] Will assume transactional DDL.
  20260819_0001 (head)

  $ docker run --rm 64b568f179980ea7443e759d2e85d97a67b76bc1f682932930a103e6a4db44ac python -m scripts.investigate --help
  usage: investigate.py [-h] [--limit LIMIT] [--repo-path REPO_PATH]
                        repo_name query
  Run retrieval, grounding, generation, parsing, and persistence for one
  repository query.
  positional arguments:
    repo_name             Repository name stored in the database
    query                 Natural-language question to investigate
  options:
    -h, --help            show this help message and exit
    --limit LIMIT         Maximum hybrid-search results to consider
    --repo-path REPO_PATH Local repository root used by the literal grep fallback
  ```

- `git status --short`:

  ```text
   M .env.example
   M README.md
   M app/config.py
   M app/main.py
   M docker/Dockerfile
   M scripts/investigate.py
  ?? app/api.py
  ?? app/api_security.py
  ?? docs/phase9-production-api.md
  ?? tests/unit/test_api.py
  ```

  No `.env` file, secret values, temporary helpers, or evaluation files appear in status. The temporary `scripts/_phase9_serve.py` helper was deleted; `evaluation/_snapshot` is absent; no `scripts/_*.py` or `evaluation/_*.py` temporary helper remains.
- Protected-file check: `git diff -- app/investigation/guard.py app/investigation/prompt.py app/investigation/generation.py app/investigation/parsing.py app/investigation/graph.py evaluation` returned no output (empty diff). Phase 8 evaluation source and results were not modified.
- Historical Windows startup-hook checks (before the requested reversion): direct startup and health passed; 36 unit tests and Ruff passed. The attempted full suite failed at the PostgreSQL integration test because `localhost:5432` was unavailable. Those results do not verify the current app-level-guard-only configuration. The fresh full suite and live route check are blocked until the Compose database reports healthy.

---

## After all checkpoints

Do not commit or push; that happens separately, reviewed with the
maintainer. This is the last phase on the current roadmap -- do not start
a Phase 10 or invent new scope. Finish with a short report: what changed,
every real request/response example from Checkpoint 9, and anything that
could not be verified.
