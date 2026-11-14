"""Custom Application Middlewares: RequestID, AccessLog, SecurityHeaders, BodySizeLimit."""

import json
import time
import uuid
from collections.abc import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp, Receive, Scope, Send

from app.core.logging import get_logger, request_id_ctx

access_logger = get_logger("app.access")


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generates or propagates X-Request-ID across the entire request/response lifecycle."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        incoming_id = request.headers.get("X-Request-ID")
        if incoming_id and incoming_id.strip():
            req_id = incoming_id.strip()
        else:
            req_id = uuid.uuid4().hex

        request.state.request_id = req_id
        token = request_id_ctx.set(req_id)
        try:
            response: Response = await call_next(request)
            response.headers["X-Request-ID"] = req_id
            return response
        finally:
            request_id_ctx.reset(token)


class BodySizeLimitMiddleware:
    """Enforces payload size limits (default 1 MB, 10 MB for file uploads).

    Rejects requests early via Content-Length or streaming byte counter
    to prevent memory exhaustion.
    """

    def __init__(
        self,
        app: ASGIApp,
        default_limit: int = 1_048_576,  # 1 MB
        upload_limit: int = 10_485_760,  # 10 MB
    ) -> None:
        self.app = app
        self.default_limit = default_limit
        self.upload_limit = upload_limit

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        method = scope.get("method", "GET").upper()
        if method not in ("POST", "PUT", "PATCH"):
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        if "/assets" in path:
            limit = 5 * 1024 * 1024  # 5 MB for exam assets
        elif "/upload" in path:
            limit = self.upload_limit
        else:
            limit = self.default_limit

        headers = dict(scope.get("headers", []))
        content_length_raw = headers.get(b"content-length")
        req_id_raw = headers.get(b"x-request-id")
        req_id = req_id_raw.decode("latin1") if req_id_raw else uuid.uuid4().hex

        # 1. Quick check via Content-Length header
        if content_length_raw:
            try:
                content_length = int(content_length_raw.decode("latin1"))
                if content_length > limit:
                    await self._send_413_response(send, limit, req_id)
                    return
            except ValueError:
                pass

        # 2. Guard against chunked / streaming transfers without Content-Length
        received_bytes = 0

        async def limited_receive() -> dict:
            nonlocal received_bytes
            message = await receive()
            if message["type"] == "http.request":
                body_chunk = message.get("body", b"")
                received_bytes += len(body_chunk)
                if received_bytes > limit:
                    raise BodySizeLimitExceededError(limit, req_id)
            return message

        try:
            await self.app(scope, limited_receive, send)
        except BodySizeLimitExceededError as exc:
            await self._send_413_response(send, exc.limit, exc.req_id)

    async def _send_413_response(self, send: Send, limit: int, req_id: str) -> None:
        limit_mb = limit // (1024 * 1024)
        error_payload = {
            "error": {
                "code": "request_entity_too_large",
                "message": f"Kích thước yêu cầu vượt quá giới hạn cho phép ({limit_mb} MB).",
                "details": None,
            }
        }
        body = json.dumps(error_payload, ensure_ascii=False).encode("utf-8")
        headers = [
            (b"content-type", b"application/json"),
            (b"content-length", str(len(body)).encode("ascii")),
            (b"x-request-id", req_id.encode("latin1")),
        ]
        await send(
            {
                "type": "http.response.start",
                "status": 413,
                "headers": headers,
            }
        )
        await send(
            {
                "type": "http.response.body",
                "body": body,
            }
        )


class BodySizeLimitExceededError(Exception):
    def __init__(self, limit: int, req_id: str) -> None:
        self.limit = limit
        self.req_id = req_id
        super().__init__("Body size limit exceeded")


class AccessLogMiddleware(BaseHTTPMiddleware):
    """Records structured access logs for each HTTP transaction."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        req_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        client_ip = request.client.host if request.client else "unknown"
        user_id = getattr(request.state, "user_id", None)

        access_logger.info(
            "HTTP %s %s -> %s (%sms)",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
                "client_ip": client_ip,
                "request_id": req_id,
                "user_id": user_id,
            },
        )

        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforces standard web security headers and no-store caching for API endpoints."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Baseline defensive security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent browser caching of sensitive business API responses
        path = request.url.path
        if path.startswith("/api") or path.startswith("/readyz"):
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"

        return response
