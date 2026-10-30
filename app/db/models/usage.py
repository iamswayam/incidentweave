"""Provider usage log ORM model."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ProviderUsageLog(Base):
    """Provider call metadata without prompt or response content."""

    __tablename__ = "provider_usage_log"
    __table_args__ = (
        CheckConstraint(
            "status IN ('success', 'failure')",
            name="ck_provider_usage_log_status",
        ),
        CheckConstraint(
            "(status = 'success' AND error_class IS NULL) OR "
            "(status = 'failure' AND error_class IS NOT NULL)",
            name="ck_provider_usage_log_status_error_class",
        ),
        Index("ix_provider_usage_log_created_at", "created_at"),
        Index(
            "ix_provider_usage_log_provider_model_status",
            "provider",
            "model",
            "status",
        ),
    )

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
    )
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    model: Mapped[str] = mapped_column(String(100), nullable=False)
    operation_tag: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(10), nullable=False)
    error_class: Mapped[str | None] = mapped_column(String(30))
    attempt_count: Mapped[int] = mapped_column(Integer, nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    correlation_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
