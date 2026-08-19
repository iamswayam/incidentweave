# IncidentWeave

IncidentWeave is a repository-aware AI incident investigation platform for backend systems.

## Phase 1

Phase 1 establishes the repository and development environment only:

- FastAPI application skeleton
- Docker Compose development environment
- PostgreSQL with pgvector container
- Environment configuration convention
- pytest and Ruff configuration
- GitHub Actions CI skeleton

Database schema, repository indexing, embeddings, retrieval, Gemini investigation, tools,
grounding, confidence, audit logging, evaluation, and product-facing CLI/API features are
implemented in their later phases.

## Local development

Create a virtual environment and install the project with development dependencies:

```bash
python -m venv .venv
# activate .venv using the command for your shell
pip install -e ".[dev]"
```

Run checks:

```bash
ruff check .
pytest
```

Run the API locally:

```bash
uvicorn app.main:app --reload
```

The health endpoint is available at `GET /health`.

## Docker Compose

Start the Phase 1 development environment:

```bash
docker compose up --build
```

PostgreSQL with pgvector is provided by the `db` service. The application currently exposes
only the Phase 1 health endpoint; database application logic is introduced in Phase 2.
