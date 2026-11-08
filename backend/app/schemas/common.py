"""Common Pydantic Schemas for System Endpoints and Standardized Errors."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    """Specific field-level validation error detail."""

    field: str = Field(description="Tên trường bị lỗi (hoặc body)")
    message: str = Field(description="Nội dung mô tả lỗi bằng tiếng Việt")
    type: str | None = Field(default=None, description="Mã kiểu lỗi (Pydantic error type)")


class ErrorBody(BaseModel):
    """Standardized error payload wrapper."""

    code: str = Field(description="Mã lỗi định danh (snake_case)")
    message: str = Field(description="Mô tả lỗi thân thiện với người dùng")
    details: Any = Field(default=None, description="Chi tiết lỗi bổ sung nếu có")


class ErrorResponse(BaseModel):
    """Root error response container."""

    error: ErrorBody


class HealthResponse(BaseModel):
    """Liveness probe response model."""

    status: str = Field(default="ok", description="Trạng thái ứng dụng")
    app: str = Field(default="quiz-backend", description="Tên dịch vụ")


class ReadyResponse(BaseModel):
    """Readiness probe response model."""

    status: str = Field(default="ready", description="Trạng thái sẵn sàng")
    database: str = Field(default="connected", description="Trạng thái kết nối CSDL")


class ServerTimeResponse(BaseModel):
    """Authoritative business clock synchronization response model."""

    server_now: str = Field(
        description="Thời gian UTC ISO-8601 định dạng Z (ví dụ: 2026-11-08T08:00:00Z)"
    )
    epoch_ms: int = Field(description="Dấu thời gian Unix tính bằng mili-giây")

