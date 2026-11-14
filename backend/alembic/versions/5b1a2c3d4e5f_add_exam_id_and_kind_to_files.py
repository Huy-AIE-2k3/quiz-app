"""add_exam_id_and_kind_to_files

Revision ID: 5b1a2c3d4e5f
Revises: 4a92c31e5f8b
Create Date: 2026-11-14 10:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "5b1a2c3d4e5f"
down_revision: str | Sequence[str] | None = "4a92c31e5f8b"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add exam_id foreign key and kind column to files table."""
    op.add_column(
        "files",
        sa.Column("exam_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "files",
        sa.Column(
            "kind",
            sa.String(length=32),
            server_default="question_image",
            nullable=False,
        ),
    )
    op.create_foreign_key(
        op.f("fk_files_exam_id_exams"),
        "files",
        "exams",
        ["exam_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index(op.f("ix_files_exam_id"), "files", ["exam_id"], unique=False)
    op.create_index(op.f("ix_files_kind"), "files", ["kind"], unique=False)


def downgrade() -> None:
    """Remove exam_id and kind columns from files table."""
    op.drop_index(op.f("ix_files_kind"), table_name="files")
    op.drop_index(op.f("ix_files_exam_id"), table_name="files")
    op.drop_constraint(op.f("fk_files_exam_id_exams"), "files", type_="foreignkey")
    op.drop_column("files", "kind")
    op.drop_column("files", "exam_id")
