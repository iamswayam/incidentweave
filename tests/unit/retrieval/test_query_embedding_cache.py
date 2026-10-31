from __future__ import annotations

from app.db.models import QueryEmbeddingCache
from app.retrieval.query_embedding_cache import (
    build_query_embedding_key,
    normalize_query,
    validate_cached_vector,
)


def test_normalize_query_collapses_whitespace_and_preserves_case() -> None:
    assert normalize_query(" \tHow  Does\nAPI work? \r\n") == "How Does API work?"


def test_cache_key_identity_includes_model_task_dimensions_and_query() -> None:
    key = build_query_embedding_key("model-a", "default", 768, "How are you?")

    assert key != build_query_embedding_key("model-b", "default", 768, "How are you?")
    assert key != build_query_embedding_key("model-a", "document", 768, "How are you?")
    assert key != build_query_embedding_key("model-a", "default", 512, "How are you?")
    assert key != build_query_embedding_key("model-a", "default", 768, "How am I?")
    assert key == build_query_embedding_key("model-a", "default", 768, " How  are you? ")


def test_cache_key_does_not_retain_or_serialize_query_text() -> None:
    query = "sensitive unique phrase"
    key = build_query_embedding_key("model-a", "default", 3, query)

    assert query not in repr(key)
    assert {column.name for column in QueryEmbeddingCache.__table__.columns} == {
        "id",
        "embedding_model",
        "task_type",
        "dimensions",
        "query_hash",
        "vector",
        "created_at",
    }


def test_validate_cached_vector_accepts_only_matching_numeric_dimensions() -> None:
    assert validate_cached_vector([0, 0.5, 1], 3) == [0.0, 0.5, 1.0]
    assert validate_cached_vector([0.0, 1.0], 3) is None
    assert validate_cached_vector([0.0, True, 1.0], 3) is None
    assert validate_cached_vector([0.0, float("nan"), 1.0], 3) is None
    assert validate_cached_vector("not a vector", 3) is None
