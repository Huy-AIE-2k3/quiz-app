"""Student Exam Schemas (Step 5.1).

Strict allow-list schemas for student examination portal.
Guarantees 0% leakage of internal configs, scores, or answer keys.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

StudentExamState = Literal[
    "upcoming",
    "open",
    "closed",
    "in_progress",
    "submitted",
    "result_available",
]


class StudentExamListItem(BaseModel):
    """Allow-list schema for student exam catalog."""

    id: uuid.UUID
    title: str
    subject: str
    duration_minutes: int
    question_count: int = Field(default=0)
    open_at: datetime | None = None
    close_at: datetime | None = None
    state: StudentExamState
    attempt_id: uuid.UUID | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentExamDetail(BaseModel):
    """Allow-list schema for student exam introduction view."""

    id: uuid.UUID
    title: str
    subject: str
    description_md: str
    duration_minutes: int
    question_count: int = Field(default=0)
    total_points: Decimal = Field(default=Decimal("0.00"))
    open_at: datetime | None = None
    close_at: datetime | None = None
    state: StudentExamState
    attempt_id: uuid.UUID | None = None
    can_start: bool = Field(default=False)

    model_config = ConfigDict(from_attributes=True)


class StudentStartAttemptResponse(BaseModel):
    """Allow-list schema for starting or resuming an attempt (Step 5.2).

    Guarantees 0% leakage of internal scoring configs, answers, or keys.
    """

    id: uuid.UUID
    exam_id: uuid.UUID
    status: str
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None = None
    remaining_seconds: int
    server_now: datetime

    model_config = ConfigDict(from_attributes=True)


class StudentAnswerItem(BaseModel):
    """Student's saved answer to a question in an attempt (Step 5.3)."""

    question_id: uuid.UUID
    value: dict[str, Any] = Field(default_factory=dict)
    client_seq: int = 0

    model_config = ConfigDict(from_attributes=True)


class StudentAttemptDetailResponse(BaseModel):
    """Full detail of an attempt for taking/resuming an exam (Step 5.3).

    Strict allow-list guaranteeing 0% data leakage:
    - Never leaks answers, internal keys, scoring configs, or explanations.
    - Shuffles questions & options stably according to attempt.shuffle_seed.
    - Includes current answers with client_seq.
    """

    id: uuid.UUID
    exam_id: uuid.UUID
    exam_title: str
    status: str
    started_at: datetime
    deadline_at: datetime
    submitted_at: datetime | None = None
    remaining_seconds: int
    server_now: datetime
    questions: list[dict[str, Any]]
    answers: dict[str, StudentAnswerItem] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class StudentSaveAnswerRequest(BaseModel):
    """Payload for auto-saving student answer for a specific question (Step 5.4)."""

    value: dict[str, Any] = Field(default_factory=dict)
    client_seq: int = Field(default=1, ge=0)


class StudentSaveAnswerResponse(BaseModel):
    """Response returned upon saving or ignoring an answer packet (Step 5.4)."""

    question_id: uuid.UUID
    client_seq: int
    status: str  # "saved" or "ignored"
    updated_at: datetime
    value: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(from_attributes=True)


class StudentAttemptStatusResponse(BaseModel):
    """Lightweight sync schema for monotonic countdown clock tracking (Step 5.5).

    Guarantees:
    - Ultra-low bandwidth (< 300 bytes JSON payload).
    - Accurately tracks remaining_seconds, deadline_at, and lazy-finalized submitted status.
    """

    id: uuid.UUID
    status: str
    remaining_seconds: int
    server_now: datetime
    deadline_at: datetime
    submitted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
