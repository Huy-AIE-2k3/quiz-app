"""Authentication Endpoints: Login, Session Inspection, and Logout."""

from datetime import timedelta

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.dependencies import get_bearer_token, get_current_user
from app.core.errors import AppError
from app.core.logging import get_logger
from app.core.security import (
    check_failed_login_rate_limit,
    clear_failed_logins,
    generate_session_token,
    hash_token,
    record_failed_login,
    verify_dummy_password,
    verify_password,
)
from app.core.time import get_clock
from app.db.session import get_db
from app.models import Session as SessionModel
from app.models import User
from app.schemas.auth import LoginRequest, LoginResponse, UserResponse

logger = get_logger("app.auth")
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])


def _extract_client_ip(request: Request) -> str:
    """Extracts client IP prioritizing X-Forwarded-For if behind trusted proxy."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "127.0.0.1"


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginResponse:
    """Authenticates user with username and password, issuing a 12-hour sliding session token.

    Security features:
        - Timing attack resistance via constant-time dummy verification.
        - Rate limiting per (IP + username) preventing brute force.
        - Argon2id password verification bounded by concurrency semaphore.
        - Stores only SHA-256 hash of the 32-byte token in the database.
    """
    client_ip = _extract_client_ip(request)
    username_clean = payload.username.strip().lower()

    # 1. Enforce rate limiting: max 10 failed attempts / minute per (IP + username)
    check_failed_login_rate_limit(client_ip, username_clean)

    # 2. Look up user by lowercase username
    user = db.execute(select(User).where(User.username == username_clean)).scalar_one_or_none()

    if not user:
        # User not found: run dummy verify to ensure response time matches failed password check
        verify_dummy_password(payload.password)
        record_failed_login(client_ip, username_clean)
        logger.warning(
            "Đăng nhập thất bại: tên đăng nhập không tồn tại",
            extra={"username": username_clean, "ip": client_ip},
        )
        raise AppError(
            code="invalid_credentials",
            message="Sai tên đăng nhập hoặc mật khẩu.",
            status_code=401,
        )

    # 3. User found: verify real password
    if not verify_password(user.hashed_password, payload.password):
        record_failed_login(client_ip, username_clean)
        logger.warning(
            "Đăng nhập thất bại: sai mật khẩu",
            extra={"username": username_clean, "ip": client_ip},
        )
        raise AppError(
            code="invalid_credentials",
            message="Sai tên đăng nhập hoặc mật khẩu.",
            status_code=401,
        )

    # 4. Check account status only after password verification succeeded
    if not user.is_active:
        logger.warning(
            "Đăng nhập thất bại: tài khoản đã bị khóa",
            extra={"username": username_clean, "ip": client_ip},
        )
        raise AppError(
            code="account_disabled",
            message="Tài khoản đã bị tạm khóa. Vui lòng liên hệ giáo viên quản trị.",
            status_code=403,
        )

    # 5. Success: clear failed login counter for this (IP, username) pair
    clear_failed_logins(client_ip, username_clean)

    # 6. Generate 32-byte session token and compute SHA-256 digest
    raw_token = generate_session_token()
    token_digest = hash_token(raw_token)

    settings = get_settings()
    now = get_clock().now()
    expires_at = now + timedelta(hours=settings.SESSION_TTL_HOURS)
    user_agent = request.headers.get("User-Agent")

    # 7. Persist session record
    session_record = SessionModel(
        user_id=user.id,
        token_hash=token_digest,
        created_at=now,
        expires_at=expires_at,
        last_seen_at=now,
        user_agent=user_agent[:512] if user_agent else None,
        ip_address=client_ip[:45],
    )
    db.add(session_record)
    db.commit()

    logger.info(
        "Đăng nhập thành công",
        extra={"user_id": str(user.id), "username": user.username, "role": user.role},
    )

    return LoginResponse(
        access_token=raw_token,
        token_type="bearer",
        role=user.role,
        user_id=user.id,
        username=user.username,
        full_name=user.full_name,
        expires_at=expires_at,
    )


@router.get("/me", response_model=UserResponse, status_code=status.HTTP_200_OK)
def get_me(user: User = Depends(get_current_user)) -> UserResponse:
    """Returns profile identity of the currently authenticated user."""
    return UserResponse(
        id=user.id,
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(
    token: str = Depends(get_bearer_token),
    db: Session = Depends(get_db),
) -> dict:
    """Terminates current session by deleting the session token record."""
    token_digest = hash_token(token)
    db.execute(delete(SessionModel).where(SessionModel.token_hash == token_digest))
    db.commit()
    return {"status": "ok", "message": "Đăng xuất thành công."}
