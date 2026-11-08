"""Pydantic Schemas for Authentication and User Profiles."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Payload for user login."""

    username: str = Field(..., min_length=1, max_length=64, description="Tên đăng nhập")
    password: str = Field(..., min_length=1, max_length=255, description="Mật khẩu tài khoản")


class LoginResponse(BaseModel):
    """Response returned upon successful authentication."""

    access_token: str = Field(..., description="Raw 32-byte URL-safe bearer token")
    token_type: str = Field(default="bearer", description="Token type")
    role: str = Field(..., description="Vai trò: admin | student")
    user_id: uuid.UUID = Field(..., description="ID người dùng")
    username: str = Field(..., description="Tên đăng nhập chữ thường")
    full_name: str = Field(..., description="Họ và tên người dùng")
    expires_at: datetime = Field(..., description="Thời điểm hết hạn phiên làm việc")


class UserResponse(BaseModel):
    """Public user identity profile."""

    id: uuid.UUID
    username: str
    full_name: str
    role: str
    is_active: bool
    created_at: datetime
