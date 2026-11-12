"""Question Model."""

import uuid
from decimal import Decimal
from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import JSON

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.exam import Exam


class Question(Base):
    """Question item supporting 5 formats (mcq, tf, short_text, short_number, file_upload)."""

    __tablename__ = "questions"

    __table_args__ = (
        CheckConstraint(
            "question_type IN ('mcq', 'tf', 'true_false', "
            "'short_text', 'short_number', 'short_answer', 'file_upload')",
            name="ck_questions_question_type",
        ),
        CheckConstraint("points > 0 AND points <= 100", name="ck_questions_points_range"),
        UniqueConstraint(
            "exam_id",
            "position",
            name="uq_questions_exam_position",
            deferrable=True,
            initially="DEFERRED",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    exam_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exams.id", ondelete="CASCADE"), nullable=False, index=True
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
    question_type: Mapped[str] = mapped_column(String(32), nullable=False)
    content_md: Mapped[str] = mapped_column(Text, nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default="{}",
    )
    answer_key: Mapped[dict[str, Any]] = mapped_column(
        JSON().with_variant(postgresql.JSONB, "postgresql"),
        nullable=False,
        default=dict,
        server_default="{}",
    )
    explanation_md: Mapped[str | None] = mapped_column(Text, nullable=True)
    points: Mapped[Decimal] = mapped_column(
        Numeric(6, 2), nullable=False, default=Decimal("1.00"), server_default="1.00"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="questions")
    answers: Mapped[list["Answer"]] = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )
