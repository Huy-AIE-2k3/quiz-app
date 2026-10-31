import logging
import time
import uuid

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.logging import request_id_ctx, user_id_ctx

logger = logging.getLogger("app.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that:
    1. Extracts or generates a unique `X-Request-ID` (UUID) for every incoming request.
    2. Injects the request ID into contextvars for transparent logging.
    3. Attaches `X-Request-ID` to the outgoing HTTP response headers.
    4. Logs structured execution metrics: method, path, status, duration_ms, client_ip, user_id.
    5. Strictly omits sensitive payloads (passwords, tokens, bodies).
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # 1. Trace ID extraction or generation
        incoming_id = request.headers.get("X-Request-ID")
        request_id = incoming_id.strip() if incoming_id and incoming_id.strip() else str(uuid.uuid4())

        token = request_id_ctx.set(request_id)
        user_token = user_id_ctx.set(None)
        request.state.request_id = request_id

        client_ip = request.client.host if request.client else "unknown"
        start_time = time.perf_counter()

        response: Response | None = None
        try:
            response = await call_next(request)
            return response
        finally:
            duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
            status_code = response.status_code if response else 500

            # Attach header to response if available
            if response is not None:
                response.headers["X-Request-ID"] = request_id

            # Structured log record
            current_user_id = user_id_ctx.get()
            logger.info(
                f"{request.method} {request.url.path} -> {status_code} ({duration_ms}ms)",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    "client_ip": client_ip,
                    "user_id": current_user_id,
                },
            )

            # Reset context
            request_id_ctx.reset(token)
            user_id_ctx.reset(user_token)
