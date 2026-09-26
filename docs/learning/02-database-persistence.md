# Database & Persistence (Phase 2)

**Date built:** August 2026
**Status:** Working, CI-verified

## What I built

Four SQLAlchemy 2.x async ORM models — `Repository`, `Chunk`, `Investigation`,
`Audit` — backed by a single Alembic migration that enables the Postgres
`vector` extension and creates all four tables with their indexes and
constraints. `Chunk.embedding` is `VECTOR(768)`. `app/db/session.py` builds an
async engine, converts `postgresql://` URLs to `postgresql+psycopg://`, and
registers pgvector on every new connection.

## Why this design

`Audit` carries its own copy of `query`, `model`, `latency_ms`, `token_usage`,
`confidence`, and `response` — separate from `Investigation` — because it's
meant to be one row per step/tool-call *within* an investigation, not one row
per investigation. That distinction was made explicit early specifically so
Phase 5+ wouldn't have to guess later whether Audit was a duplicate of
Investigation or a genuine step-level trail.

`Chunk` already carries both code-shaped fields (`function_name`, `class_name`,
`symbol`, `line_start`/`line_end`) and log/incident-shaped fields (`service`,
`environment`, `incident_id`, `timestamp`) in one table, with `document_type`
as the discriminator between them — one table for all evidence types, rather
than separate tables per source, keeping retrieval queries from needing to
union across tables later.

## Key concept, explained simply

<!-- Write this yourself: explain what VECTOR(768) actually is and why the
dimension has to match exactly between the schema and whatever embedding
model produces the vectors — use the real Phase 4 incident (gemini-embedding-001
defaulting to 3072 dimensions) as the concrete example of what happens when
it doesn't match. -->

## Walkthrough example

The migration (`20260819_0001_initial_schema.py`) creates the `vector`
extension, then `repositories`, `chunks`, `investigations`, and
`audit_records`, with `ix_chunks_repository_id` and
`ix_chunks_repository_file_path` indexes on `chunks`. CI applies this same
migration against a freshly-started Postgres container on every run —
`alembic upgrade head` passing in CI is the actual proof this schema is
reproducible from scratch, not just working on one machine that's drifted
from what's checked in.

## What I found, not from reading the code but from actually tracing it

At the time this phase was originally built, nothing in the application layer
read or wrote to `chunks` — only the schema and a single integration test
(`test_database.py`) touched it, to validate persistence. That gap (real
schema, zero real usage) is exactly what Phase 3 and 4 closed.

## Interview-ready summary (3-4 sentences)

<!-- Write this yourself, once the "key concept" section is filled in. -->
