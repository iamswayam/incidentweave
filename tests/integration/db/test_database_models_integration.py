"""Integration tests for Phase 2 ORM model metadata."""

import pytest

from app.db.base import Base
from app.db.models import (
    Audit,
    Chunk,
    IngestRun,
    Investigation,
    QueryEmbeddingCache,
)

pytestmark = pytest.mark.integration


def test_all_phase_2_models_are_registered() -> None:
    """Verify all approved ORM models are present in SQLAlchemy metadata."""

    expected_tables = {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
        "ingest_runs",
        "query_embedding_cache",
    }

    assert expected_tables.issubset(Base.metadata.tables)
    assert Audit.__tablename__ == "audit_records"
    assert Chunk.__tablename__ == "chunks"
    assert IngestRun.__tablename__ == "ingest_runs"
    assert Investigation.__tablename__ == "investigations"
    assert QueryEmbeddingCache.__tablename__ == "query_embedding_cache"
