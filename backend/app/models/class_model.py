"""Class and ClassMember Models."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Uuid, false, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.exam import ExamClass
    from app.models.user import User


class Class(Base):
    """Classroom or cohort grouping students."""

    __tablename__ = "classes"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    academic_year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_archived: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=false()
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    members: Mapped[list["ClassMember"]] = relationship(
        "ClassMember", back_populates="class_", cascade="all, delete-orphan"
    )
    exam_assignments: Mapped[list["ExamClass"]] = relationship(
        "ExamClass", back_populates="class_", cascade="all, delete-orphan"
    )


class ClassMember(Base):
    """Association table linking students to classes with composite primary key."""

    __tablename__ = "class_members"

    class_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("classes.id", ondelete="CASCADE"), primary_key=True
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    class_: Mapped["Class"] = relationship("Class", back_populates="members")
    student: Mapped["User"] = relationship("User", back_populates="class_memberships")
