# Project Setup (Phase 1)

**Date built:** August 2026
**Status:** Working, CI-verified

## What I built

The project skeleton: a FastAPI app (`app/main.py`) exposing `/health`, a
`pyproject.toml` pinning a minimal dependency set (FastAPI, Pydantic Settings,
Uvicorn, SQLAlchemy 2.x, psycopg3, pgvector, Alembic — dev-only: httpx, pytest,
Ruff), Docker Compose running a `pgvector/pgvector:pg17` Postgres service
alongside the app, and a GitHub Actions CI pipeline that spins up the same
Postgres+pgvector image as a service container, runs Ruff, applies Alembic
migrations, runs pytest, and builds the Docker image.

## Why this design

Dependency ranges are pinned to major-version-safe bounds (e.g.
`sqlalchemy>=2.0,<3.0`) rather than exact versions — room for patch/minor
updates without silently jumping a breaking major version. CI uses the exact
same `pgvector/pgvector:pg17` image as local Docker Compose, so there's no
"works in CI but not locally" (or vice versa) gap from mismatched Postgres
versions.

## Key concept, explained simply

<!-- Write this yourself: explain why CI running a real Postgres+pgvector
service container (not a mock) matters for a project whose correctness
depends on actual pgvector query behavior — connect it to why we insisted on
running real embedding/retrieval commands throughout this project instead of
trusting descriptions of what should happen. -->

## Walkthrough example

CI pipeline, in order, on every push: checkout → set up Python 3.12 → install
`.[dev]` → `ruff check .` → verify Postgres is reachable (both `pg_isready`
and a raw socket connection check) → `alembic upgrade head` → `pytest` →
`docker build -f docker/Dockerfile .`. All 8 steps currently pass.

## What I found, not from reading the code but from actually tracing it

The Dockerfile only `COPY`s `pyproject.toml` and `app/` — it does not copy
`scripts/`, `alembic.ini`, or `migrations/`, and installs `.` rather than
`.[dev]`. The built image can currently serve `/health` and nothing else;
running the ingestion/embedding scripts or a migration inside the container
would fail. CI's Docker step only checks that the image *builds*, not that
anything runs inside it, so this gap exists without failing any check. Not
fixed yet — flagged as a real, known limitation rather than something to
silently work around later.

## Interview-ready summary (3-4 sentences)

<!-- Write this yourself, once the "key concept" section is filled in. -->
