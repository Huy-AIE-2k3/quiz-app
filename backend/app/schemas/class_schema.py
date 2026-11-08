"""Pydantic Schemas for Class Management."""

import re
import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

CLASS_CODE_REGEX = re.compile(r"^[A-Z0-9_-]{2,20}$")


class ClassBase(BaseModel):
    """Base schema for Class."""

    name: str = Field(..., min_length=1, max_length=255, description="Tên lớp học")
    academic_year: int = Field(..., ge=2000, le=2100, description="Năm học")
    subject: Literal["toan", "tin", "both"] = Field(
        default="both", description="Môn học: toan, tin, hoặc both"
    )


class ClassCreate(ClassBase):
    """Schema for creating a new classroom."""

    code: str = Field(..., description="Mã lớp duy nhất (2-20 ký tự chữ hoa, số, dấu gạch)")

    @field_validator("code", mode="before")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        if isinstance(value, str):
            normalized = value.strip().upper()
            if not CLASS_CODE_REGEX.match(normalized):
                raise ValueError(
                    "Mã lớp phải có độ dài 2-20 ký tự và chỉ chứa chữ cái, "
                    "số, dấu gạch nối hoặc gạch dưới."
                )
            return normalized
        return value


class ClassUpdate(BaseModel):
    """Schema for updating an existing classroom with optimistic locking version."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    academic_year: int | None = Field(default=None, ge=2000, le=2100)
    subject: Literal["toan", "tin", "both"] | None = None
    is_archived: bool | None = None
    version: int = Field(
        ...,
        description="Phiên bản hiện tại phục vụ khóa lạc quan (Optimistic Locking)",
    )


class ClassResponse(ClassBase):
    """Response schema representing a classroom with membership metrics."""

    id: uuid.UUID
    code: str
    is_archived: bool
    version: int
    created_at: datetime
    student_count: int = Field(default=0, description="Số lượng học sinh trong lớp")
    exam_count: int = Field(default=0, description="Số lượng đề thi đã giao cho lớp")

    model_config = ConfigDict(from_attributes=True)


class ClassListResponse(BaseModel):
    """Paginated response list of classrooms."""

    items: list[ClassResponse]
    total: int
    limit: int
    offset: int
