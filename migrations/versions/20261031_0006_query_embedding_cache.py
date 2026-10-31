"""Add persistent query embedding cache."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20261031_0006"
down_revision: str | None = "20261030_0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the query-derived vector cache without retaining query text."""

    op.create_table(
        "query_embedding_cache",
        sa.Column("id", sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column("embedding_model", sa.String(length=100), nullable=False),
        sa.Column("task_type", sa.String(length=40), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False),
        sa.Column("query_hash", sa.String(length=64), nullable=False),
        sa.Column("vector", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("dimensions > 0", name="ck_query_embedding_cache_dimensions"),
    )
    op.create_index(
        "uq_query_embedding_cache_identity",
        "query_embedding_cache",
        ["embedding_model", "task_type", "dimensions", "query_hash"],
        unique=True,
    )
    op.create_index(
        "ix_query_embedding_cache_created_at",
        "query_embedding_cache",
        ["created_at"],
    )


def downgrade() -> None:
    """Drop the persistent query embedding cache."""

    op.drop_index(
        "ix_query_embedding_cache_created_at",
        table_name="query_embedding_cache",
    )
    op.drop_index(
        "uq_query_embedding_cache_identity",
        table_name="query_embedding_cache",
    )
    op.drop_table("query_embedding_cache")
