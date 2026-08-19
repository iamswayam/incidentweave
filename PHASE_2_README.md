# IncidentWeave V1 - Phase 2 Database & Persistence

This package contains the complete Phase 2 database foundation only.

## Included

- SQLAlchemy 2.x async engine/session
- psycopg 3 PostgreSQL driver
- pgvector SQLAlchemy support
- centralized declarative Base
- approved ORM models:
  - Repository
  - Chunk
  - Investigation
  - Audit
- `VECTOR(768)` chunk embedding column
- pgvector extension migration
- foundational foreign-key and access-path indexes
- Alembic configuration and initial migration
- unit tests for model metadata
- PostgreSQL/pgvector persistence integration test

## Not included

No Phase 3+ functionality is included:

- repository ingestion
- AST/Markdown/log chunking
- Gemini embeddings
- vector retrieval
- PostgreSQL Full-Text Search
- RRF
- Gemini investigation
- grounding
- confidence calculation
- controlled tools
- audit workflow logic
- evaluation
- production CLI/API

## Installation

Merge the provided `pyproject.toml` content with the existing Phase 1 file, then:

```powershell
pip install -e ".[dev]"
```

Start PostgreSQL:

```powershell
docker compose up -d db
```

Run the migration:

```powershell
alembic upgrade head
```

Run checks:

```powershell
ruff check .
pytest
pytest -m integration
```

The integration test is intentionally separate because it requires a running PostgreSQL instance with the migration applied.
