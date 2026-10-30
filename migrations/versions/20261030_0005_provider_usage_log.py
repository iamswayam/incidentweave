"""Add provider usage log table."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261030_0005"
down_revision: str | None = "20261026_0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create provider usage telemetry table without payload text."""

    op.create_table(
        "provider_usage_log",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model", sa.String(length=100), nullable=False),
        sa.Column("operation_tag", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=10), nullable=False),
        sa.Column("error_class", sa.String(length=30), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("correlation_id", sa.String(length=64), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('success', 'failure')",
            name="ck_provider_usage_log_status",
        ),
        sa.CheckConstraint(
            "(status = 'success' AND error_class IS NULL) OR "
            "(status = 'failure' AND error_class IS NOT NULL)",
            name="ck_provider_usage_log_status_error_class",
        ),
    )
    op.create_index(
        "ix_provider_usage_log_created_at",
        "provider_usage_log",
        ["created_at"],
    )
    op.create_index(
        "ix_provider_usage_log_provider_model_status",
        "provider_usage_log",
        ["provider", "model", "status"],
    )


def downgrade() -> None:
    """Drop provider usage telemetry table."""

    op.drop_index(
        "ix_provider_usage_log_provider_model_status",
        table_name="provider_usage_log",
    )
    op.drop_index(
        "ix_provider_usage_log_created_at",
        table_name="provider_usage_log",
    )
    op.drop_table("provider_usage_log")
