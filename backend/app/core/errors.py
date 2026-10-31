import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app.error")


class AppError(Exception):
    """
    Base application exception.
    All custom domain exceptions must inherit from this class.
    """

    def __init__(
        self,
        code: str = "app_error",
        message: str = "Đã xảy ra lỗi trong quá trình xử lý",
        status_code: int = status.HTTP_400_BAD_REQUEST,
        details: Any = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "code": self.code,
            "message": self.message,
        }
        if self.details is not None:
            result["details"] = self.details
        return result


class Unauthorized(AppError):
    """401 Unauthorized"""

    def __init__(
        self,
        message: str = "Chưa đăng nhập hoặc phiên làm việc đã hết hạn",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="unauthorized",
            message=message,
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details,
        )


class Forbidden(AppError):
    """403 Forbidden"""

    def __init__(
        self,
        message: str = "Bạn không có quyền thực hiện hành động này",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="forbidden",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class NotFound(AppError):
    """404 Not Found"""

    def __init__(
        self,
        message: str = "Không tìm thấy tài nguyên yêu cầu",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="not_found",
            message=message,
            status_code=status.HTTP_404_NOT_FOUND,
            details=details,
        )


class AttemptClosed(AppError):
    """409 Conflict: Attempt is already finalized or deadline passed"""

    def __init__(
        self,
        message: str = "Phiên làm bài đã kết thúc hoặc đã nộp",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="attempt_closed",
            message=message,
            status_code=status.HTTP_409_CONFLICT,
            details=details,
        )


class ExamNotOpen(AppError):
    """403 Forbidden: Exam is not in open time window"""

    def __init__(
        self,
        message: str = "Bài thi chưa mở hoặc đã kết thúc",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="exam_not_open",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
            details=details,
        )


class ValidationFailed(AppError):
    """422 Unprocessable Entity"""

    def __init__(
        self,
        message: str = "Dữ liệu không hợp lệ. Vui lòng kiểm tra lại các trường.",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="validation_error",
            message=message,
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            details=details,
        )


class RateLimited(AppError):
    """429 Too Many Requests"""

    def __init__(
        self,
        message: str = "Bạn đã gửi quá nhiều yêu cầu. Vui lòng thử lại sau.",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="rate_limited",
            message=message,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            details=details,
        )


class DatabaseUnavailable(AppError):
    """503 Service Unavailable: Database connectivity loss"""

    def __init__(
        self,
        message: str = "Dịch vụ cơ sở dữ liệu tạm thời không khả dụng. Vui lòng thử lại.",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="db_unavailable",
            message=message,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            details=details,
        )


class InternalServerError(AppError):
    """500 Internal Server Error"""

    def __init__(
        self,
        message: str = "Đã xảy ra lỗi hệ thống nội bộ. Vui lòng thử lại sau.",
        details: Any = None,
    ) -> None:
        super().__init__(
            code="internal_error",
            message=message,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details,
        )


def _translate_pydantic_error(err_type: str, msg: str) -> str:
    """Translates common Pydantic validation errors into clear Vietnamese."""
    translations = {
        "missing": "Trường này là bắt buộc",
        "value_error.missing": "Trường này là bắt buộc",
        "string_too_short": "Độ dài văn bản quá ngắn",
        "string_too_long": "Độ dài văn bản vượt quá giới hạn",
        "int_parsing": "Giá trị phải là số nguyên hợp lệ",
        "int_type": "Giá trị phải là số nguyên",
        "float_parsing": "Giá trị phải là số thực hợp lệ",
        "float_type": "Giá trị phải là số thực",
        "bool_parsing": "Giá trị phải là đúng/sai (boolean)",
        "bool_type": "Giá trị phải là đúng/sai (boolean)",
        "json_invalid": "Định dạng JSON không hợp lệ",
        "uuid_parsing": "Mã định danh UUID không đúng định dạng",
        "datetime_parsing": "Thời gian không đúng định dạng ISO chuẩn",
    }
    for prefix, vi_msg in translations.items():
        if err_type.startswith(prefix):
            return vi_msg
    return msg


def register_error_handlers(app: FastAPI) -> None:
    """Registers unified error handlers to enforce consistent JSON schema across API."""

    @app.exception_handler(AppError)
    async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.to_dict()},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        details: list[dict[str, str]] = []
        for error in exc.errors():
            loc = [str(x) for x in error.get("loc", []) if x != "body"]
            field = ".".join(loc) if loc else "body"
            err_type = error.get("type", "")
            raw_msg = error.get("msg", "Dữ liệu không hợp lệ")
            friendly_msg = _translate_pydantic_error(err_type, raw_msg)
            details.append({"field": field, "message": friendly_msg})

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={
                "error": {
                    "code": "validation_error",
                    "message": "Dữ liệu yêu cầu không hợp lệ. Vui lòng kiểm tra lại các trường.",
                    "details": details,
                }
            },
        )

    @app.exception_handler(StarletteHTTPException)
    async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code_map = {
            status.HTTP_404_NOT_FOUND: "not_found",
            status.HTTP_403_FORBIDDEN: "forbidden",
            status.HTTP_401_UNAUTHORIZED: "unauthorized",
            status.HTTP_405_METHOD_NOT_ALLOWED: "method_not_allowed",
        }
        code = code_map.get(exc.status_code, "http_error")
        message = str(exc.detail) if exc.detail else "Đã xảy ra lỗi HTTP"
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {"code": code, "message": message}},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
        # Crucial: Log full stack trace internally, but strictly conceal it from client response
        logger.exception("Unhandled Exception caught by global error handler: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "internal_error",
                    "message": "Đã xảy ra lỗi hệ thống nội bộ. Vui lòng thử lại sau.",
                }
            },
        )
