"""add_version_and_subject_to_classes

Revision ID: 2ea37ae90c62
Revises: 01432629931d
Create Date: 2026-11-08 11:18:00.356553

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "2ea37ae90c62"
down_revision: str | Sequence[str] | None = "01432629931d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "classes", sa.Column("subject", sa.String(length=32), server_default="both", nullable=False)
    )
    op.add_column("classes", sa.Column("version", sa.Integer(), server_default="1", nullable=False))
    op.create_check_constraint(
        "ck_classes_subject", "classes", "subject IN ('toan', 'tin', 'both')"
    )
    op.create_check_constraint("ck_classes_code_min_len", "classes", "length(code) >= 2")


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_classes_code_min_len", "classes", type_="check")
    op.drop_constraint("ck_classes_subject", "classes", type_="check")
    op.drop_column("classes", "version")
    op.drop_column("classes", "subject")
