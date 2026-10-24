"""Ingestion run ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class IngestRun(Base):
    """Provenance and configuration for one repository ingestion."""

    __tablename__ = "ingest_runs"
    __table_args__ = (Index("ix_ingest_runs_repository_id", "repository_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    repository_id: Mapped[int] = mapped_column(
        ForeignKey("repositories.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_path: Mapped[str] = mapped_column(Text, nullable=False)
    git_remote: Mapped[str | None] = mapped_column(Text)
    commit_sha: Mapped[str | None] = mapped_column(String(40))
    dirty: Mapped[bool | None] = mapped_column(Boolean)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    chunker_version: Mapped[str] = mapped_column(String(50), nullable=False)
    embedding_model: Mapped[str | None] = mapped_column(String(100))
