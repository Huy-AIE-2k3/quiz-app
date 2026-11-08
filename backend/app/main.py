"""FastAPI Application Main Entry Point & Factory."""

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import OperationalError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.middleware.gzip import GZipMiddleware

from app.core.config import get_settings
from app.core.errors import (
    AppError,
    app_error_handler,
    http_exception_handler,
    operational_error_handler,
    unhandled_exception_handler,
    validation_error_handler,
)
from app.core.logging import setup_logging
from app.core.middleware import (
    AccessLogMiddleware,
    BodySizeLimitMiddleware,
    RequestIDMiddleware,
    SecurityHeadersMiddleware,
)
from app.routers import admin_router, auth_router, student_router, system_router
from app.routers.dev import router as dev_router


def create_app() -> FastAPI:
    """Application factory for FastAPI instance."""
    settings = get_settings()

    # Configure structured JSON logging with redaction
    setup_logging(level="DEBUG" if settings.DEBUG else "INFO")

    app = FastAPI(
        title="Quiz Toán - Tin API",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url=None,
    )

    # Register centralized exception handlers
    app.add_exception_handler(AppError, app_error_handler)  # type: ignore
    app.add_exception_handler(RequestValidationError, validation_error_handler)  # type: ignore
    app.add_exception_handler(OperationalError, operational_error_handler)  # type: ignore
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)  # type: ignore
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # Configure ASGI Middleware stack (executed outside-in)
    # Execution order on Request:
    # RequestID -> BodySizeLimit -> AccessLog -> SecurityHeaders -> CORS -> GZip -> Router
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(AccessLogMiddleware)
    app.add_middleware(
        BodySizeLimitMiddleware,
        default_limit=1_048_576,  # 1 MB default
        upload_limit=settings.MAX_UPLOAD_MB * 1024 * 1024,
    )
    app.add_middleware(RequestIDMiddleware)

    # Register API Routers
    app.include_router(auth_router)
    app.include_router(admin_router)
    app.include_router(student_router)
    app.include_router(system_router)

    # Include development/diagnostic routes for testing and staging
    if settings.APP_ENV in ("development", "test") or settings.DEBUG:
        app.include_router(dev_router)

    return app


app = create_app()
