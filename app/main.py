"""FastAPI application entry point for IncidentWeave."""

from fastapi import FastAPI

app = FastAPI(title="IncidentWeave")


@app.get("/health")
def health() -> dict[str, str]:
    """Return a minimal application health response."""

    return {"status": "ok"}
