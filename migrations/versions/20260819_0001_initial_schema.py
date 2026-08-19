"""Create IncidentWeave Phase 2 database schema."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import VECTOR
from sqlalchemy.dialects import postgresql

revision: str = "20260819_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create the Phase 2 database schema."""

    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "repositories",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.UniqueConstraint("name", name="uq_repositories_name"),
    )

    op.create_table(
        "chunks",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(length=1024), nullable=False),
        sa.Column("file_type", sa.String(length=100)),
        sa.Column("document_type", sa.String(length=100)),
        sa.Column("symbol", sa.String(length=255)),
        sa.Column("function_name", sa.String(length=255)),
        sa.Column("class_name", sa.String(length=255)),
        sa.Column("line_start", sa.Integer()),
        sa.Column("line_end", sa.Integer()),
        sa.Column("section", sa.String(length=500)),
        sa.Column("service", sa.String(length=255)),
        sa.Column("environment", sa.String(length=100)),
        sa.Column("incident_id", sa.String(length=255)),
        sa.Column("timestamp", sa.DateTime(timezone=True)),
        sa.Column("embedding", VECTOR(768)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_chunks_repository_id",
        "chunks",
        ["repository_id"],
    )
    op.create_index(
        "ix_chunks_repository_file_path",
        "chunks",
        ["repository_id", "file_path"],
    )

    op.create_table(
        "investigations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("response", sa.Text()),
        sa.Column("model", sa.String(length=255)),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("token_usage", sa.Integer()),
        sa.Column("confidence", sa.String(length=50)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_investigations_repository_id",
        "investigations",
        ["repository_id"],
    )

    op.create_table(
        "audit_records",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("investigation_id", sa.Integer(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("repository_id", sa.Integer(), nullable=False),
        sa.Column(
            "retrieved_chunk_ids",
            postgresql.ARRAY(sa.Integer()),
        ),
        sa.Column(
            "vector_scores",
            postgresql.ARRAY(sa.Float()),
        ),
        sa.Column(
            "fts_scores",
            postgresql.ARRAY(sa.Float()),
        ),
        sa.Column(
            "rrf_scores",
            postgresql.ARRAY(sa.Float()),
        ),
        sa.Column("tool_calls", postgresql.JSONB()),
        sa.Column("model", sa.String(length=255)),
        sa.Column("response", sa.Text()),
        sa.Column("latency_ms", sa.Integer()),
        sa.Column("token_usage", sa.Integer()),
        sa.Column("confidence", sa.String(length=50)),
        sa.Column("user_feedback", sa.Text()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["investigation_id"],
            ["investigations.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["repository_id"],
            ["repositories.id"],
            ondelete="CASCADE",
        ),
    )


def downgrade() -> None:
    """Drop the Phase 2 database schema."""

    op.drop_table("audit_records")
    op.drop_index(
        "ix_investigations_repository_id",
        table_name="investigations",
    )
    op.drop_table("investigations")
    op.drop_index(
        "ix_chunks_repository_file_path",
        table_name="chunks",
    )
    op.drop_index(
        "ix_chunks_repository_id",
        table_name="chunks",
    )
    op.drop_table("chunks")
    op.drop_table("repositories")
    op.execute("DROP EXTENSION IF EXISTS vector")
