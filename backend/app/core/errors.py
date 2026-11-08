"""Application-wide Error Definitions & Centralized Exception Handlers."""

from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger

logger = get_logger("app.errors")


class AppError(Exception):
    """Base domain application error for predictable business exceptions."""

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: Any = None,
    ) -> None:
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)


def get_request_id(request: Request) -> str | None:
    """Helper to extract request ID from request state or headers."""
    return getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")


def make_error_response(
    code: str,
    message: str,
    status_code: int,
    details: Any = None,
    headers: dict[str, str] | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Constructs a unified, standardized JSON error response."""
    resp_headers = headers.copy() if headers else {}
    if request_id:
        resp_headers["X-Request-ID"] = request_id

    content = {
        "error": {
            "code": code,
            "message": message,
            "details": details,
        }
    }
    return JSONResponse(status_code=status_code, content=content, headers=resp_headers)


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Handler for domain-specific AppError instances."""
    req_id = get_request_id(request)
    return make_error_response(
        code=exc.code,
        message=exc.message,
        status_code=exc.status_code,
        details=exc.details,
        request_id=req_id,
    )


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handler for Pydantic schema validation failures."""
    req_id = get_request_id(request)
    formatted_errors = []
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", []) if x != "body"]
        field_name = ".".join(loc) if loc else "body"
        formatted_errors.append(
            {
                "field": field_name,
                "message": err.get("msg", "Dữ liệu không hợp lệ"),
                "type": err.get("type", "value_error"),
            }
        )

    return make_error_response(
        code="validation_error",
        message="Dữ liệu yêu cầu không hợp lệ.",
        status_code=getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422),
        details=formatted_errors,
        request_id=req_id,
    )


async def operational_error_handler(request: Request, exc: OperationalError) -> JSONResponse:
    """Handler for database connection loss or Neon serverless pause."""
    req_id = get_request_id(request)
    logger.warning("Database operational error (request_id=%s): %s", req_id, exc)
    return make_error_response(
        code="db_unavailable",
        message="Dịch vụ cơ sở dữ liệu tạm thời gián đoạn. Vui lòng thử lại sau giây lát.",
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        headers={"Retry-After": "2"},
        request_id=req_id,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handler for HTTP exceptions (404, 405, 413, etc.)."""
    req_id = get_request_id(request)
    status_code_map = {
        status.HTTP_400_BAD_REQUEST: "bad_request",
        status.HTTP_401_UNAUTHORIZED: "unauthorized",
        status.HTTP_403_FORBIDDEN: "forbidden",
        status.HTTP_404_NOT_FOUND: "not_found",
        status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE: "request_entity_too_large",
        status.HTTP_429_TOO_MANY_REQUESTS: "too_many_requests",
    }
    code = status_code_map.get(exc.status_code, f"http_{exc.status_code}")

    return make_error_response(
        code=code,
        message=str(exc.detail),
        status_code=exc.status_code,
        headers=exc.headers,
        request_id=req_id,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler for unexpected 500 errors.

    Logs full stack trace to server logs, but masks internal details from client.
    """
    req_id = get_request_id(request)
    logger.exception(
        "Unhandled server exception on %s %s (request_id=%s): %s",
        request.method,
        request.url.path,
        req_id,
        exc,
    )

    return make_error_response(
        code="internal_error",
        message="Đã xảy ra lỗi máy chủ nội bộ. Vui lòng liên hệ quản trị viên.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=req_id,
    )
