"""Exam and ExamClass Models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.attempt import Attempt
    from app.models.class_model import Class
    from app.models.file import File
    from app.models.question import Question
    from app.models.user import User


class Exam(Base):
    """Exam definition containing metadata, duration, status, and questions."""

    __tablename__ = "exams"

    __table_args__ = (
        CheckConstraint(
            "subject IN ('toan', 'tin', 'both', 'math', 'computer_science')",
            name="ck_exams_subject",
        ),
        CheckConstraint(
            "duration_minutes >= 1 AND duration_minutes <= 300",
            name="ck_exams_duration_range",
        ),
        CheckConstraint(
            "status IN ('draft', 'published', 'closed', 'archived', 'locked')",
            name="ck_exams_status",
        ),
        CheckConstraint(
            "result_visibility IN ('hidden', 'score_only', 'detailed')",
            name="ck_exams_result_visibility",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description_md: Mapped[str] = mapped_column(Text, nullable=False, default="", server_default="")
    subject: Mapped[str] = mapped_column(String(32), nullable=False, default="toan")
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=45)
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="draft", server_default="draft"
    )
    open_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    close_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    locked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    shuffle_questions: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    shuffle_options: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    result_visibility: Mapped[str] = mapped_column(
        String(32), nullable=False, default="score_only", server_default="score_only"
    )
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    creator: Mapped["User"] = relationship("User", back_populates="authored_exams")
    classes: Mapped[list["ExamClass"]] = relationship(
        "ExamClass", back_populates="exam", cascade="all, delete-orphan"
    )
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="Question.position",
    )
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="exam")
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="exam", cascade="all, delete-orphan"
    )


class ExamClass(Base):
    """Association table linking exams to classes with composite primary key."""

    __tablename__ = "exam_classes"

    exam_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("exams.id", ondelete="CASCADE"), primary_key=True
    )
    class_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )

    # Relationships
    exam: Mapped["Exam"] = relationship("Exam", back_populates="classes")
    class_: Mapped["Class"] = relationship("Class", back_populates="exam_assignments")
