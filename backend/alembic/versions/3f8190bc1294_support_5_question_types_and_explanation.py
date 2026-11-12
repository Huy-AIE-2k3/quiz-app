"""support_5_question_types_and_explanation

Revision ID: 3f8190bc1294
Revises: 2ea37ae90c62
Create Date: 2026-11-13 04:50:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "3f8190bc1294"
down_revision: str | Sequence[str] | None = "2ea37ae90c62"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema to support 5 question types and explanation."""
    # Add explanation_md column to questions table
    op.add_column("questions", sa.Column("explanation_md", sa.Text(), nullable=True))

    # Update question_type check constraint to support 5 types (plus legacy aliases)
    # Use execute to handle constraint drop safely across naming conventions
    op.execute(
        "ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_ck_questions_question_type"
    )
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_question_type")
    op.create_check_constraint(
        "ck_questions_question_type",
        "questions",
        "question_type IN ('mcq', 'tf', 'true_false', 'short_text', 'short_number', 'short_answer', 'file_upload')",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE questions DROP CONSTRAINT IF EXISTS ck_questions_question_type")
    op.create_check_constraint(
        "ck_questions_question_type",
        "questions",
        "question_type IN ('mcq', 'true_false', 'short_answer', 'file_upload')",
    )
    op.drop_column("questions", "explanation_md")
