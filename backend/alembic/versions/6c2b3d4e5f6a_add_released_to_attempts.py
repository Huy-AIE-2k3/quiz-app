"""add_released_to_attempts

Revision ID: 6c2b3d4e5f6a
Revises: 5b1a2c3d4e5f
Create Date: 2026-11-17 17:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6c2b3d4e5f6a"
down_revision: str | Sequence[str] | None = "5b1a2c3d4e5f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add released column to attempts table."""
    op.add_column(
        "attempts",
        sa.Column(
            "released",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Remove released column from attempts table."""
    op.drop_column("attempts", "released")
