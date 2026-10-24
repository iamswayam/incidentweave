"""Add replayable investigation audit fields."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261026_0004"
down_revision: str | None = "20261025_0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add nullable request and per-chunk replay details to audit records."""

    op.add_column("audit_records", sa.Column("prompt", sa.Text(), nullable=True))
    op.add_column(
        "audit_records",
        sa.Column("prompt_version", sa.String(length=50), nullable=True),
    )
    op.add_column("audit_records", sa.Column("raw_response", sa.Text(), nullable=True))
    op.add_column(
        "audit_records",
        sa.Column("raw_self_rating", sa.String(length=20), nullable=True),
    )
    op.add_column(
        "audit_records",
        sa.Column("generation_params", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "audit_records",
        sa.Column("thresholds", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "audit_records",
        sa.Column("embedding_model", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "audit_records",
        sa.Column("chunk_records", postgresql.JSONB(), nullable=True),
    )
    op.add_column(
        "audit_records",
        sa.Column("trace", postgresql.JSONB(), nullable=True),
    )


def downgrade() -> None:
    """Remove replayable investigation audit fields."""

    op.drop_column("audit_records", "trace")
    op.drop_column("audit_records", "chunk_records")
    op.drop_column("audit_records", "embedding_model")
    op.drop_column("audit_records", "thresholds")
    op.drop_column("audit_records", "generation_params")
    op.drop_column("audit_records", "raw_self_rating")
    op.drop_column("audit_records", "raw_response")
    op.drop_column("audit_records", "prompt_version")
    op.drop_column("audit_records", "prompt")
