"""Integration tests for Phase 2 ORM model metadata."""

import pytest

from app.db.base import Base
from app.db.models import Audit, Chunk, Investigation

pytestmark = pytest.mark.integration


def test_all_phase_2_models_are_registered() -> None:
    """Verify all approved ORM models are present in SQLAlchemy metadata."""

    expected_tables = {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
    }

    assert expected_tables.issubset(Base.metadata.tables)
    assert Audit.__tablename__ == "audit_records"
    assert Chunk.__tablename__ == "chunks"
    assert Investigation.__tablename__ == "investigations"
