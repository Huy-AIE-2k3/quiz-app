"""Pydantic Schemas for Exam Management and Lifecycle State Machine."""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.core.question_utils import normalize_nfc

ExamStatus = Literal["draft", "published", "closed", "archived"]
ExamSubject = Literal["toan", "tin", "both", "math", "computer_science"]
ResultVisibility = Literal["hidden", "score_only", "detailed"]


class ExamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=255)
    subject: ExamSubject = "toan"
    duration_minutes: int = Field(default=45, ge=1, le=300)
    description_md: str = Field(default="", max_length=20000)
    open_at: datetime | None = None
    close_at: datetime | None = None
    shuffle_questions: bool = False
    shuffle_options: bool = True
    result_visibility: ResultVisibility = "score_only"
    class_ids: list[uuid.UUID] = Field(default_factory=list)

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Tiêu đề bài thi không được để trống.")
        return normalize_nfc(s)

    @field_validator("description_md")
    @classmethod
    def validate_desc(cls, v: str) -> str:
        return normalize_nfc(v.strip())

    @model_validator(mode="after")
    def validate_time_window(self) -> "ExamCreate":
        if self.open_at and self.close_at and self.open_at >= self.close_at:
            raise ValueError("Thời điểm mở đề (open_at) phải trước thời điểm đóng đề (close_at).")
        return self


class ExamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=1, max_length=255)
    subject: ExamSubject | None = None
    duration_minutes: int | None = Field(default=None, ge=1, le=300)
    description_md: str | None = Field(default=None, max_length=20000)
    open_at: datetime | None = None
    close_at: datetime | None = None
    shuffle_questions: bool | None = None
    shuffle_options: bool | None = None
    result_visibility: ResultVisibility | None = None
    class_ids: list[uuid.UUID] | None = None
    version: int = Field(..., description="Optimistic locking version")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = v.strip()
        if not s:
            raise ValueError("Tiêu đề bài thi không được để trống.")
        return normalize_nfc(s)

    @model_validator(mode="after")
    def validate_time_window(self) -> "ExamUpdate":
        if self.open_at and self.close_at and self.open_at >= self.close_at:
            raise ValueError("Thời điểm mở đề (open_at) phải trước thời điểm đóng đề (close_at).")
        return self


class ExamStatusTransition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: ExamStatus
    version: int = Field(..., description="Optimistic locking version")


class ExamReorderQuestions(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ordered_ids: list[uuid.UUID] = Field(..., min_length=1)


class ExamAssignClassesPayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    class_ids: list[uuid.UUID] = Field(default_factory=list)


class ExamValidationSummary(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question_count: int
    total_points: Decimal
    duration_minutes: int
    class_count: int
    student_count: int


class ExamValidationResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    summary: ExamValidationSummary | None = None


class ExamPreviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description_md: str
    subject: str
    duration_minutes: int
    status: str
    shuffle_questions: bool
    shuffle_options: bool
    questions: list[dict[str, Any]]


class AssignedClassInfo(BaseModel):
    id: uuid.UUID
    name: str
    code: str
    is_archived: bool


class ExamDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    description_md: str
    subject: str
    duration_minutes: int
    status: str
    open_at: datetime | None = None
    close_at: datetime | None = None
    locked_at: datetime | None = None
    shuffle_questions: bool
    shuffle_options: bool
    result_visibility: str
    version: int
    created_by: uuid.UUID
    created_at: datetime
    assigned_classes: list[dict[str, Any]] = Field(default_factory=list)
    question_count: int = 0
    total_points: Decimal = Decimal("0.00")
    attempt_count: int = 0


class ExamListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    items: list[ExamDetailResponse]
    total: int
    limit: int
    offset: int
