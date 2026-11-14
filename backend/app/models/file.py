"""Uploaded File Metadata Model."""

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.answer import Answer
    from app.models.exam import Exam
    from app.models.user import User


class File(Base):
    """Metadata record for uploaded binary assets stored in S3/MinIO/Cloudflare R2."""

    __tablename__ = "files"

    __table_args__ = (CheckConstraint("size_bytes > 0", name="ck_files_size_bytes_positive"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    exam_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("exams.id", ondelete="CASCADE"), nullable=True, index=True
    )
    kind: Mapped[str] = mapped_column(
        String(32), server_default="question_image", nullable=False, index=True
    )
    original_name: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(512), unique=True, nullable=False, index=True)
    mime_type: Mapped[str] = mapped_column(String(128), nullable=False)
    size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="files")
    exam: Mapped["Exam | None"] = relationship("Exam", back_populates="files")
    answers: Mapped[list["Answer"]] = relationship("Answer", back_populates="file")
