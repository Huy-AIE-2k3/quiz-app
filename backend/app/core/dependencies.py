"""FastAPI Security Dependencies for Authentication, Session Resolution, and RBAC.

Implements:
    - Bearer token extraction and format validation (TC-2.3-09: invalid format -> 401).
    - Session resolution with SHA-256 hash lookup.
    - Sliding expiration with throttled DB update (every 5 minutes).
    - RBAC: require_admin and require_student dependencies (TC-2.3-07: student -> 403).
"""

from datetime import UTC, datetime, timedelta

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_token
from app.db.session import get_db
from app.models import Session as SessionModel
from app.models import User


def get_bearer_token(request: Request) -> str:
    """Extracts and validates raw Bearer token from the HTTP Authorization header."""
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AppError(
            code="missing_credentials",
            message="Yêu cầu đăng nhập để truy cập tài nguyên này.",
            status_code=401,
        )

    parts = auth_header.strip().split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1]:
        raise AppError(
            code="invalid_token_header",
            message="Header Authorization phải có định dạng 'Bearer <token>'.",
            status_code=401,
        )

    return parts[1]


def get_current_user(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> User:
    """Resolves authenticated User from active Session token with sliding expiration."""
    token_digest = hash_token(token)

    session_record = db.execute(
        select(SessionModel)
        .options(joinedload(SessionModel.user))
        .where(SessionModel.token_hash == token_digest)
    ).scalar_one_or_none()

    if not session_record or not session_record.user:
        raise AppError(
            code="invalid_session",
            message="Phiên đăng nhập không hợp lệ hoặc đã bị thu hồi.",
            status_code=401,
        )

    now = datetime.now(UTC)

    # Check session expiration
    if session_record.expires_at < now:
        db.delete(session_record)
        db.commit()
        raise AppError(
            code="session_expired",
            message="Phiên làm việc đã hết hạn. Vui lòng đăng nhập lại.",
            status_code=401,
        )

    # Check account active status
    if not session_record.user.is_active:
        raise AppError(
            code="account_disabled",
            message="Tài khoản đã bị tạm khóa.",
            status_code=401,
        )

    # Throttled sliding expiration: update last_seen_at & expires_at at most once every 5 minutes
    time_since_last_seen = (now - session_record.last_seen_at).total_seconds()
    if time_since_last_seen >= 300.0:
        settings = get_settings()
        session_record.last_seen_at = now
        session_record.expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)
        db.commit()

    return session_record.user


def require_admin(user: User = Depends(get_current_user)) -> User:
    """Enforces administrator / teacher role authorization (HTTP 403 if role != admin)."""
    if user.role != "admin":
        raise AppError(
            code="forbidden",
            message="Quyền truy cập bị từ chối: Yêu cầu quyền giáo viên / quản trị viên.",
            status_code=403,
        )
    return user


def require_student(user: User = Depends(get_current_user)) -> User:
    """Enforces student role authorization (HTTP 403 if role != student)."""
    if user.role != "student":
        raise AppError(
            code="forbidden",
            message="Quyền truy cập bị từ chối: Tài nguyên dành riêng cho học sinh.",
            status_code=403,
        )
    return user
