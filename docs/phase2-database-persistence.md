# Phase 2 — Database & Persistence

**Status:** Complete
**Depends on:** Phase 1 (app skeleton, Docker Compose, CI) — confirmed working.

---

## Checkpoint 1 — Async SQLAlchemy setup

**Task:** Establish the async database connection layer.

### Log
- `app/db/base.py` defines the shared declarative base (`Base(DeclarativeBase)`).
- `app/db/session.py` builds an async engine via `create_async_engine`,
  rewrites `postgresql://` URLs to `postgresql+psycopg://`, registers pgvector
  on every new connection (`register_vector_async`), and exposes
  `AsyncSessionLocal` / `get_db_session()` for dependency-style session
  injection.

---

## Checkpoint 2 — ORM models

**Task:** Define the four core persistence models.

### Log
- `Repository(id, name, created_at, updated_at)` — one row per ingested
  codebase, with relationships to `chunks` and `investigations`.
- `Chunk` — carries both code-shaped fields (`function_name`, `class_name`,
  `symbol`, `line_start`/`line_end`) and log/incident-shaped fields (`service`,
  `environment`, `incident_id`, `timestamp`) in one table, with
  `document_type` as the discriminator between them. `embedding` is
  `VECTOR(768)`. Indexed on `repository_id` and on `(repository_id, file_path)`.
- `Investigation(id, repository_id, query, response, model, latency_ms,
  token_usage, confidence, created_at)` — one row per investigation.
- `Audit` — deliberately carries its own `query`, `model`, `latency_ms`,
  `token_usage`, `confidence`, `response`, plus `retrieved_chunk_ids`,
  `vector_scores`, `fts_scores`, `rrf_scores`, and `tool_calls`. This is one
  row per step/tool-call *within* an investigation, not a duplicate of
  `Investigation` — decided explicitly at this phase so later phases
  wouldn't have to guess which table owns step-level detail.

---

## Checkpoint 3 — Alembic migration

**Task:** Version-control the schema.

### Log
- Single migration (`20260819_0001_initial_schema.py`) enables the Postgres
  `vector` extension and creates `repositories`, `chunks`, `investigations`,
  and `audit_records` with their constraints and indexes, plus a `downgrade()`.
- `alembic upgrade head` running clean in CI against a freshly-started
  Postgres container (not a machine that's drifted from what's checked in)
  is the actual proof this schema is reproducible from scratch.

---

## Checkpoint 4 — Integration tests

**Task:** Validate the schema actually persists correctly against real Postgres.

### Log
- `tests/integration/test_database.py` creates and persists real
  `Repository`/`Chunk` rows against a live Postgres+pgvector instance,
  validating connectivity, the `vector` extension, `VECTOR(768)` support,
  and relationship integrity.
- **Found while documenting this phase:** at the end of Phase 2, this test
  was the *only* code touching the `chunks` table — no application code read
  or wrote to it yet. Schema existed; nothing used it. That gap is exactly
  what Phase 3 closed.

---

## Checkpoint 5 — CI database integration

**Task:** Run the above against a real database in CI, not a mock.

### Log
- CI runs the same `pgvector/pgvector:pg17` image used locally as a service
  container, applies the real migration, then runs the full test suite
  against it. No mocked DB layer anywhere in the test suite.

---

## After all checkpoints

Phase 2 produced a real, version-controlled, CI-verified schema — but a
schema with no consumer yet. Phase 3 is what made `chunks` actually get
written to.
