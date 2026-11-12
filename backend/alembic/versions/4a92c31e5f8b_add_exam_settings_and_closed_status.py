"""add_exam_settings_and_closed_status

Revision ID: 4a92c31e5f8b
Revises: 3f8190bc1294
Create Date: 2026-11-13 04:56:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4a92c31e5f8b"
down_revision: str | Sequence[str] | None = "3f8190bc1294"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to add exam configuration columns and update constraints."""
    op.add_column(
        "exams",
        sa.Column("shuffle_questions", sa.Boolean(), server_default="false", nullable=False),
    )
    op.add_column(
        "exams",
        sa.Column("shuffle_options", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "exams",
        sa.Column(
            "result_visibility",
            sa.String(length=32),
            server_default="score_only",
            nullable=False,
        ),
    )

    # Drop old constraints
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_ck_exams_status")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_status")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_ck_exams_subject")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_subject")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_ck_exams_duration_positive")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_duration_positive")

    # Add new updated constraints
    op.create_check_constraint(
        "ck_exams_status",
        "exams",
        "status IN ('draft', 'published', 'closed', 'archived', 'locked')",
    )
    op.create_check_constraint(
        "ck_exams_subject",
        "exams",
        "subject IN ('toan', 'tin', 'both', 'math', 'computer_science')",
    )
    op.create_check_constraint(
        "ck_exams_duration_range",
        "exams",
        "duration_minutes >= 1 AND duration_minutes <= 300",
    )
    op.create_check_constraint(
        "ck_exams_result_visibility",
        "exams",
        "result_visibility IN ('hidden', 'score_only', 'detailed')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_result_visibility")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_duration_range")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_subject")
    op.execute("ALTER TABLE exams DROP CONSTRAINT IF EXISTS ck_exams_status")

    op.create_check_constraint(
        "ck_exams_status",
        "exams",
        "status IN ('draft', 'published', 'locked', 'archived')",
    )
    op.create_check_constraint(
        "ck_exams_subject",
        "exams",
        "subject IN ('math', 'computer_science')",
    )
    op.create_check_constraint(
        "ck_exams_duration_positive",
        "exams",
        "duration_minutes > 0",
    )

    op.drop_column("exams", "result_visibility")
    op.drop_column("exams", "shuffle_options")
    op.drop_column("exams", "shuffle_questions")
