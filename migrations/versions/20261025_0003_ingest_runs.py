"""Add ingestion provenance and content-addressed chunk identity."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261025_0003"
down_revision: str | None = "20261024_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Record ingestion runs and establish content-based chunk identity."""

    op.create_table(
        "ingest_runs",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "repository_id",
            sa.Integer(),
            sa.ForeignKey("repositories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("git_remote", sa.Text()),
        sa.Column("commit_sha", sa.String(length=40)),
        sa.Column("dirty", sa.Boolean()),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("chunker_version", sa.String(length=50), nullable=False),
        sa.Column("embedding_model", sa.String(length=100)),
    )
    op.create_index(
        "ix_ingest_runs_repository_id",
        "ingest_runs",
        ["repository_id"],
    )

    op.add_column(
        "chunks",
        sa.Column(
            "ingest_run_id",
            sa.Integer(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )
    op.add_column(
        "chunks",
        sa.Column("content_hash", sa.String(length=64), nullable=True),
    )
    op.execute(
        "UPDATE chunks "
        "SET content_hash = encode(sha256(convert_to(content, 'UTF8')), 'hex')"
    )
    op.alter_column("chunks", "content_hash", nullable=False)
    op.create_index(
        "uq_chunks_identity",
        "chunks",
        ["repository_id", "file_path", "line_start", "line_end", "content_hash"],
        unique=True,
    )

    op.add_column(
        "audit_records",
        sa.Column(
            "ingest_run_id",
            sa.Integer(),
            sa.ForeignKey("ingest_runs.id", ondelete="SET NULL"),
            nullable=True,
        ),
    )


def downgrade() -> None:
    """Remove ingestion provenance and content-addressed chunk identity."""

    op.drop_column("audit_records", "ingest_run_id")
    op.drop_index("uq_chunks_identity", table_name="chunks")
    op.drop_column("chunks", "content_hash")
    op.drop_column("chunks", "ingest_run_id")
    op.drop_index("ix_ingest_runs_repository_id", table_name="ingest_runs")
    op.drop_table("ingest_runs")
