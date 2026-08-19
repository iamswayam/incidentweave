# IncidentWeave

**Repository-aware AI incident investigation platform for backend systems.**

IncidentWeave is a backend/AI engineering project designed to investigate production incidents by combining repository context, operational evidence, retrieval, and AI-assisted investigation.

The system is being built incrementally with a focus on reliable retrieval, evidence grounding, controlled investigation, and auditable results.

---

## Project Status

IncidentWeave is currently under active V1 development.

| Phase | Description | Status |
|---|---|---|
| Phase 1 | Project Setup | ✅ Complete |
| Phase 2 | Database & Persistence | ✅ Complete |
| Phase 3 | Repository Ingestion & Chunking | 🔜 Next |
| Phase 4 | Embeddings & Retrieval | Planned |
| Phase 5 | Investigation Engine | Planned |
| Phase 6 | Grounding & Confidence | Planned |
| Phase 7 | Controlled Tools & Audit | Planned |
| Phase 8 | Evaluation | Planned |
| Phase 9 | Production CLI / API | Planned |

### Phase 1 - Project Setup

Established the development and application foundation:

- FastAPI application
- Docker Compose environment
- PostgreSQL + pgvector
- Environment configuration
- pytest and Ruff
- GitHub Actions CI

### Phase 2 - Database & Persistence

Established the application persistence foundation:

- SQLAlchemy 2.x async integration
- PostgreSQL database integration
- Alembic migrations
- Centralized ORM models
- Repository, chunk, investigation, and audit persistence models
- pgvector support
- `VECTOR(768)` embedding storage
- Database indexes and relationships
- PostgreSQL integration tests
- CI database integration

**Current milestone: Phase 2 complete.**

---

## Architecture

IncidentWeave follows a phased architecture in which each subsystem is introduced when required by the implementation roadmap.

```text
Repository & Operational Evidence
                │
                ▼
     Repository Ingestion
        & Chunking
                │
                ▼
      PostgreSQL + pgvector
                │
                ▼
      Retrieval & Ranking
                │
                ▼
    AI-Assisted Investigation
                │
                ▼
   Grounding & Confidence
                │
                ▼
       Tools & Audit
                │
                ▼
      Evaluation & API
```

The architecture is intentionally developed incrementally to avoid introducing infrastructure or abstractions before they are required.

---

## Technology Stack

### Backend

- Python
- FastAPI
- Pydantic Settings
- Uvicorn

### Persistence

- PostgreSQL
- pgvector
- SQLAlchemy 2.x
- Psycopg 3
- Alembic

### Development & Quality

- Docker
- Docker Compose
- pytest
- Ruff
- GitHub Actions

### Planned AI & Retrieval

Later phases will introduce the approved AI and retrieval components, including:

- Gemini
- Gemini Embeddings
- Vector retrieval
- PostgreSQL Full-Text Search
- Hybrid retrieval / Reciprocal Rank Fusion (RRF)
- Investigation orchestration
- Grounding
- Confidence scoring
- Controlled investigation tools
- Evaluation

---

## Database

The application persistence layer uses PostgreSQL with pgvector.

The current persistence model includes:

- `Repository`
- `Chunk`
- `Investigation`
- `Audit`

Chunks support source metadata such as repository association, file paths, line ranges, and chunk content. The schema also provides a 768-dimensional vector column for the later embedding and retrieval phases.

```text
embedding VECTOR(768)
```

The PostgreSQL `vector` extension is enabled through the version-controlled Alembic migration system.

Database persistence and schema behavior are covered by integration tests.

---

## Project Structure

```text
incidentweave/
├── app/
│   ├── api/
│   ├── core/
│   ├── db/
│   │   ├── models/
│   │   │   ├── audit.py
│   │   │   ├── chunk.py
│   │   │   ├── investigation.py
│   │   │   └── repository.py
│   │   ├── base.py
│   │   └── session.py
│   ├── ingestion/
│   ├── retrieval/
│   ├── investigation/
│   └── main.py
│
├── migrations/
│   └── versions/
│
├── tests/
│   ├── integration/
│   └── unit/
│
├── .github/
│   └── workflows/
│
├── alembic.ini
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

Components are introduced as their respective implementation phases begin.

---

## Local Development

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate the virtual environment.

On Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 2. Install the project

```bash
pip install -e ".[dev]"
```

### 3. Configure environment variables

Copy the example environment file:

```powershell
Copy-Item .env.example .env
```

Update the values in `.env` for your local environment.

Do not commit `.env` or any credentials.

### 4. Start the development environment

```bash
docker compose up --build
```

This starts the application and PostgreSQL + pgvector services.

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Run the API locally

```bash
uvicorn app.main:app --reload
```

The current health endpoint is:

```text
GET /health
```

---

## Testing

IncidentWeave uses both unit and integration tests.

### Run the complete test suite

```bash
pytest
```

### Run unit tests

```bash
pytest tests/unit
```

### Run integration tests

Integration tests require a running PostgreSQL + pgvector database.

```bash
pytest tests/integration
```

### Static analysis

Run Ruff with:

```bash
ruff check .
```

The integration tests validate the actual PostgreSQL persistence layer, including:

- PostgreSQL connectivity
- pgvector extension availability
- `VECTOR(768)` schema support
- SQLAlchemy persistence
- Repository/chunk relationships

---

## Database Migrations

Alembic manages database schema changes.

Apply the latest migrations:

```bash
alembic upgrade head
```

Show the current migration revision:

```bash
alembic current
```

Show migration history:

```bash
alembic history
```

Schema changes should be introduced through version-controlled migrations rather than manual database modifications.

---

## Continuous Integration

GitHub Actions validates the project on pushes and pull requests.

The CI pipeline currently performs:

1. Python environment setup
2. Dependency installation
3. Ruff checks
4. PostgreSQL + pgvector startup
5. PostgreSQL health verification
6. Alembic migrations
7. Unit and integration tests
8. Docker image build

Integration tests therefore run against a real PostgreSQL + pgvector service in CI.

---

## Engineering Principles

IncidentWeave is developed with the following engineering principles:

- Incremental, phase-based implementation
- Explicit and maintainable Python
- Thin API and CLI boundaries
- Business logic kept outside transport layers
- Infrastructure concerns kept isolated
- Database migrations tracked in version control
- Evidence-first investigation
- Retrieval before generation
- Explicit grounding and confidence
- Automated verification before phase completion
- No premature infrastructure or abstraction

The project intentionally avoids introducing technologies or architectural layers before they are required by the approved implementation plan.

---

## V1 Scope Discipline

IncidentWeave V1 is intentionally developed without prematurely introducing deferred technologies or infrastructure.

Examples of technologies outside the current implementation scope include:

- LangGraph
- Redis / Celery
- MCP
- S3
- Vision AI
- Kubernetes
- Elasticsearch
- Pinecone
- Weaviate
- Authentication

These boundaries help keep the V1 implementation focused and maintainable.

---

## Roadmap

```text
01  Project Setup
        │
        ▼
02  Database & Persistence
        │
        ▼
03  Repository Ingestion & Chunking
        │
        ▼
04  Embeddings & Retrieval
        │
        ▼
05  Investigation Engine
        │
        ▼
06  Grounding & Confidence
        │
        ▼
07  Controlled Tools & Audit
        │
        ▼
08  Evaluation
        │
        ▼
09  Production CLI / API
```

**Completed:** Phases 1 and 2

**Next:** Phase 3 - Repository Ingestion & Chunking

---

## Current Verification

Phase 2 has been verified locally and through GitHub Actions.

```text
Ruff                     PASS
PostgreSQL               PASS
pgvector                 PASS
Alembic migration        PASS
VECTOR(768)              PASS
SQLAlchemy persistence   PASS
Test suite               8 passed
GitHub Actions           PASS
```

The test environment currently reports one non-blocking FastAPI/Starlette `httpx` deprecation warning.

---

## License

This project is currently maintained as a personal backend/AI engineering portfolio project.
