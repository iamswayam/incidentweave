# Phase 1 — Project Setup

Note: this log was reconstructed after the phase was completed, from the repository state and verified history; it was not written step-by-step during development.

**Status:** Complete
**Depends on:** nothing — this is the foundation phase.

---

## Checkpoint 1 — FastAPI application skeleton

**Task:** Stand up a minimal FastAPI app with a health check endpoint.

### Log
- `app/main.py` creates `app = FastAPI(title="IncidentWeave")` and exposes
  `GET /health` returning `{"status": "ok"}`. Nothing else is wired into the
  API yet — deliberately, per V1 scope discipline.

---

## Checkpoint 2 — Dependency management & tooling

**Task:** Define project dependencies and code quality tooling.

### Log
- `pyproject.toml` pins core dependencies with major-version-safe ranges:
  `fastapi>=0.115,<1.0`, `pydantic-settings>=2.7,<3.0`, `uvicorn[standard]>=0.34,<1.0`,
  `sqlalchemy>=2.0,<3.0`, `psycopg[binary]>=3.2,<4.0`, `pgvector>=0.3,<1.0`,
  `alembic>=1.15,<2.0`. Dev-only extras: `httpx`, `pytest`, `ruff`.
- Ruff configured for Python 3.12, 100-char line length, `E`/`F`/`I` rule
  selection, double-quote/space formatting.
- `[tool.pytest.ini_options]` sets `testpaths = ["tests"]` and defines an
  `integration` marker for tests requiring a real Postgres instance.

---

## Checkpoint 3 — Docker Compose local environment

**Task:** Provide a local Postgres + pgvector environment matching what CI
and production will use.

### Log
- `docker-compose.yml` runs `pgvector/pgvector:pg17` as the `db` service
  (port 5432, healthcheck via `pg_isready`) and builds the app from
  `docker/Dockerfile` as the `app` service, depending on `db`'s healthcheck.
- Using the *same* pgvector image tag here as in CI (Checkpoint 4) was a
  deliberate choice to avoid a "works locally, breaks in CI" or
  "works in CI, breaks locally" gap from mismatched Postgres/pgvector versions.

---

## Checkpoint 4 — CI pipeline

**Task:** Automate verification on every push/PR.

### Log
- GitHub Actions (`ci.yml`) runs a `pgvector/pgvector:pg17` service container
  alongside the job, then: checkout → set up Python 3.12 → `pip install -e ".[dev]"`
  → `ruff check .` → verify Postgres reachable (`pg_isready` + a raw TCP
  socket check) → `alembic upgrade head` → `pytest` → `docker build -f docker/Dockerfile .`.
- All 8 steps currently pass on every push.

---

## Checkpoint 5 — Container build

**Task:** Produce a runnable Docker image for the app.

### Log
- `docker/Dockerfile` is `python:3.12-slim`, copies only `pyproject.toml` and
  `app/`, runs `pip install --no-cache-dir .` (production deps only, no dev
  extras), exposes port 8000, and runs `uvicorn app.main:app`.
- **Found while documenting this phase, not during original development:**
  the image does not copy `scripts/`, `alembic.ini`, or `migrations/`. The
  built image can currently serve `/health` and nothing else — running the
  ingestion/embedding scripts or a migration *inside* the container would
  fail, since those files aren't present in it. CI's Docker step only
  verifies the image *builds*, not that anything runs inside it, so this
  gap exists without failing any check. Flagged as a known limitation, not
  yet fixed — revisit before any real deployment.

---

## After all checkpoints

Phase 1 provides the skeleton every later phase builds on: a working app,
a reproducible local + CI environment, and quality gates. No AI/retrieval
code exists yet at the end of this phase.
