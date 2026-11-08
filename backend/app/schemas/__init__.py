"""Pydantic Schemas Package."""

from app.schemas.class_schema import (
    ClassCreate,
    ClassListResponse,
    ClassResponse,
    ClassUpdate,
)
from app.schemas.common import (
    ErrorBody,
    ErrorDetail,
    ErrorResponse,
    HealthResponse,
    ReadyResponse,
    ServerTimeResponse,
)
from app.schemas.student_schema import (
    ClassSimple,
    EnrollmentRequest,
    EnrollmentResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
    StudentCreate,
    StudentDetailResponse,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)

__all__ = [
    "ClassCreate",
    "ClassListResponse",
    "ClassResponse",
    "ClassSimple",
    "ClassUpdate",
    "EnrollmentRequest",
    "EnrollmentResponse",
    "ErrorBody",
    "ErrorDetail",
    "ErrorResponse",
    "HealthResponse",
    "ReadyResponse",
    "ResetPasswordRequest",
    "ResetPasswordResponse",
    "ServerTimeResponse",
    "StudentCreate",
    "StudentDetailResponse",
    "StudentListResponse",
    "StudentResponse",
    "StudentUpdate",
]
