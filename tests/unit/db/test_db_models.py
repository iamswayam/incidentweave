from pgvector.sqlalchemy import VECTOR

from app.db.base import Base
from app.db.models import Audit, Chunk, IngestRun, Investigation


def test_all_database_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
        "ingest_runs",
        "provider_usage_log",
        "query_embedding_cache",
    }


def test_chunk_embedding_is_768_dimensions() -> None:
    column = Chunk.__table__.c.embedding

    assert isinstance(column.type, VECTOR)
    assert column.type.dim == 768


def test_chunk_has_required_content_hash_and_ingest_run_reference() -> None:
    columns = Chunk.__table__.c

    assert columns.content_hash.type.length == 64
    assert columns.content_hash.nullable is False
    assert columns.ingest_run_id.nullable is True
    assert columns.ingest_run_id.foreign_keys.pop().ondelete == "SET NULL"
    assert IngestRun.__tablename__ == "ingest_runs"
    assert Audit.__table__.c.ingest_run_id.nullable is True


def test_investigation_outcome_columns_are_registered() -> None:
    columns = Investigation.__table__.c

    assert columns.outcome.type.length == 32
    assert columns.outcome.nullable is False
    assert columns.outcome.server_default is not None
    assert columns.error_class.type.length == 100
    assert columns.error_class.nullable is True


def test_phase2_relationships_are_defined() -> None:
    assert Chunk.repository.property.back_populates == "chunks"
    assert Investigation.repository.property.back_populates == "investigations"
    assert Audit.investigation.property.back_populates == "audit_records"


def test_required_chunk_indexes_exist() -> None:
    index_names = {index.name for index in Chunk.__table__.indexes}

    assert "ix_chunks_repository_id" in index_names
    assert "ix_chunks_repository_file_path" in index_names
    assert "uq_chunks_identity" in index_names
