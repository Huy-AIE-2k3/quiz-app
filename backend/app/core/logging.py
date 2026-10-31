import json
import logging
import sys
from contextvars import ContextVar
from typing import Any

from app.core.time import utcnow

# Context variables for request tracing
request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)
user_id_ctx: ContextVar[str | None] = ContextVar("user_id_ctx", default=None)


class JSONLogFormatter(logging.Formatter):
    """
    Formatter that outputs structured JSON log records for production and log aggregators.
    Includes request_id and user_id from context variables if available.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Contextual request tracing
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()
        if req_id:
            log_data["request_id"] = req_id

        usr_id = getattr(record, "user_id", None) or user_id_ctx.get()
        if usr_id:
            log_data["user_id"] = usr_id

        # Standard HTTP middleware extra attributes
        for field in ("method", "path", "status_code", "duration_ms", "client_ip"):
            val = getattr(record, field, None)
            if val is not None:
                log_data[field] = val

        # Exception information if present
        if record.exc_info:
            log_data["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(log_level: str = "INFO") -> None:
    """Configures application-wide structured JSON logging to stdout."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Avoid duplicate handlers if called multiple times
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(handler)

    # Silence overly verbose third-party loggers in dev
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
