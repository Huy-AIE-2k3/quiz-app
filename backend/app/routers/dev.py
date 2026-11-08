"""Development and Diagnostic Test Router.

Enabled in non-production environments to verify error handling,
validation, logging, and middleware limits.
"""

from fastapi import APIRouter, Header, status
from pydantic import BaseModel, Field
from sqlalchemy.exc import OperationalError

from app.core.errors import AppError
from app.core.logging import get_logger

router = APIRouter(prefix="/api/v1/dev", tags=["Development & Diagnostics"])
logger = get_logger("app.dev")


class EchoRequest(BaseModel):
    name: str = Field(min_length=2, description="Tên đối tượng")
    count: int = Field(ge=1, description="Số lượng")


class LoginTestRequest(BaseModel):
    username: str
    password: str


@router.get("/app-error")
def trigger_app_error() -> None:
    """Explicitly triggers a custom AppError with 409 Conflict status."""
    raise AppError(
        code="conflict_error",
        message="Xung đột tài nguyên kiểm thử.",
        status_code=status.HTTP_409_CONFLICT,
        details={"conflict_key": "resource_123"},
    )


@router.get("/boom")
def trigger_unhandled_boom() -> None:
    """Explicitly triggers an unhandled RuntimeError to test 500 masking."""
    raise RuntimeError("boom: secret database internal pointer failure")


@router.get("/db-error")
def trigger_db_error() -> None:
    """Simulates SQLAlchemy OperationalError (e.g. Neon sleep or network drop)."""
    raise OperationalError(
        "SELECT 1",
        {},
        Exception("psycopg.OperationalError: server closed the connection"),
    )


@router.post("/echo")
def echo_payload(data: EchoRequest) -> dict:
    """Validates schema and echoes back data."""
    return {"message": "ok", "data": data.model_dump()}


@router.post("/login-test")
def login_test(data: LoginTestRequest, authorization: str | None = Header(default=None)) -> dict:
    """Logs sensitive credentials to verify that JSONFormatter & SensitiveDataFilter scrub them."""
    logger.info(
        "Attempting dev login for username=%s password=%s auth=%s",
        data.username,
        data.password,
        authorization,
    )
    return {"status": "authenticated", "username": data.username}


@router.post("/upload")
def upload_test(data: dict) -> dict:
    """Simulates an upload endpoint subject to higher MAX_UPLOAD_MB limits."""
    return {"status": "uploaded", "size": len(str(data))}
