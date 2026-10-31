"""Persistent cache for query-derived embedding vectors."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class QueryEmbeddingCache(Base):
    """Cache query embeddings without retaining their source query text."""

    __tablename__ = "query_embedding_cache"
    __table_args__ = (
        CheckConstraint("dimensions > 0", name="ck_query_embedding_cache_dimensions"),
        Index(
            "uq_query_embedding_cache_identity",
            "embedding_model",
            "task_type",
            "dimensions",
            "query_hash",
            unique=True,
        ),
        Index("ix_query_embedding_cache_created_at", "created_at"),
    )

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    embedding_model: Mapped[str] = mapped_column(String(100), nullable=False)
    task_type: Mapped[str] = mapped_column(String(40), nullable=False)
    dimensions: Mapped[int] = mapped_column(Integer, nullable=False)
    query_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    vector: Mapped[list[float]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
