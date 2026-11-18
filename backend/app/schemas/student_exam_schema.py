"""Student Exam Schemas (Step 5.1).

Strict allow-list schemas for student examination portal.
Guarantees 0% leakage of internal configs, scores, or answer keys.
"""

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

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
