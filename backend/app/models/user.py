"""User Model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.attempt import Attempt
    from app.models.audit_log import AuditLog
    from app.models.class_model import ClassMember
    from app.models.exam import Exam
    from app.models.file import File
    from app.models.session import Session


class User(Base):
    """User account model for administrators (teachers) and students."""

    __tablename__ = "users"

    __table_args__ = (
        CheckConstraint("username = lower(username)", name="ck_users_username_lower"),
        CheckConstraint("length(username) >= 3", name="ck_users_username_min_len"),
        CheckConstraint("role IN ('admin', 'student')", name="ck_users_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(32), nullable=False, default="student")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    sessions: Mapped[list["Session"]] = relationship(
        "Session", back_populates="user", cascade="all, delete-orphan"
    )
    class_memberships: Mapped[list["ClassMember"]] = relationship(
        "ClassMember", back_populates="student", cascade="all, delete-orphan"
    )
    authored_exams: Mapped[list["Exam"]] = relationship("Exam", back_populates="creator")
    attempts: Mapped[list["Attempt"]] = relationship("Attempt", back_populates="student")
    files: Mapped[list["File"]] = relationship("File", back_populates="user")
    graded_answers: Mapped[list["Answer"]] = relationship(
        "Answer", foreign_keys="Answer.graded_by", back_populates="grader"
    )
    audit_logs: Mapped[list["AuditLog"]] = relationship("AuditLog", back_populates="user")
