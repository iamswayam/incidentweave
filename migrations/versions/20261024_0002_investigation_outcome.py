"""Add investigation outcome and sanitized error class."""

from typing import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "20261024_0002"
down_revision: str | None = "20260819_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add outcome tracking to investigations."""

    op.add_column(
        "investigations",
        sa.Column(
            "outcome",
            sa.String(length=32),
            server_default="answered",
            nullable=False,
        ),
    )
    op.add_column(
        "investigations",
        sa.Column("error_class", sa.String(length=100), nullable=True),
    )


def downgrade() -> None:
    """Remove investigation outcome tracking."""

    op.drop_column("investigations", "error_class")
    op.drop_column("investigations", "outcome")
