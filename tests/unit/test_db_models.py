from pgvector.sqlalchemy import VECTOR

from app.db.base import Base
from app.db.models import Audit, Chunk, Investigation


def test_all_phase2_models_are_registered() -> None:
    assert set(Base.metadata.tables) == {
        "repositories",
        "chunks",
        "investigations",
        "audit_records",
    }


def test_chunk_embedding_is_768_dimensions() -> None:
    column = Chunk.__table__.c.embedding

    assert isinstance(column.type, VECTOR)
    assert column.type.dim == 768


def test_phase2_relationships_are_defined() -> None:
    assert Chunk.repository.property.back_populates == "chunks"
    assert Investigation.repository.property.back_populates == "investigations"
    assert Audit.investigation.property.back_populates == "audit_records"


def test_required_chunk_indexes_exist() -> None:
    index_names = {index.name for index in Chunk.__table__.indexes}

    assert "ix_chunks_repository_id" in index_names
    assert "ix_chunks_repository_file_path" in index_names
