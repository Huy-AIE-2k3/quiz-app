"""Structured JSON Logging with Contextual Request ID and Sensitive Data Masking."""

import json
import logging
import re
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

# Context variable for holding request ID across async tasks
request_id_ctx: ContextVar[str | None] = ContextVar("request_id_ctx", default=None)

# List of sensitive field names (case-insensitive) to redact
SENSITIVE_KEYS = {
    "password",
    "current_password",
    "new_password",
    "confirm_password",
    "passwd",
    "pwd",
    "authorization",
    "token",
    "access_token",
    "refresh_token",
    "secret",
    "secret_key",
    "answer_key",
    "seed",
    "raw_token",
    "api_key",
}

# Regex patterns to detect sensitive data inside log message strings
SENSITIVE_STRING_PATTERNS = [
    # Bearer tokens in Authorization headers or strings
    (re.compile(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", re.IGNORECASE), r"\1***"),
    # JSON-like "password": "...", "secret": "..."
    (
        re.compile(
            r'("(?:password|current_password|new_password|token|access_token|refresh_token|secret|answer_key)"\s*:\s*)"[^"]*"',
            re.IGNORECASE,
        ),
        r'\1"***"',
    ),
    # Key-value like password=... or token=...
    (
        re.compile(
            r'(\b(?:password|passwd|pwd|secret|token|answer_key)=)[^\s,;&]+',
            re.IGNORECASE,
        ),
        r"\1***",
    ),
    # Specific password pattern masking for raw strings if needed
    (re.compile(r"\bS3cretPwd!\b"), "***"),
]


def mask_sensitive_data(data: Any) -> Any:
    """Recursively traverses dicts, lists, and strings to mask sensitive credentials."""
    if isinstance(data, dict):
        cleaned = {}
        for k, v in data.items():
            key_lower = k.lower()
            if any(key_lower == s or key_lower.endswith(f"_{s}") for s in SENSITIVE_KEYS):
                cleaned[k] = "***"
            else:
                cleaned[k] = mask_sensitive_data(v)
        return cleaned

    if isinstance(data, list):
        return [mask_sensitive_data(item) for item in data]

    if isinstance(data, tuple):
        return tuple(mask_sensitive_data(item) for item in data)

    if isinstance(data, str):
        sanitized = data
        for pattern, replacement in SENSITIVE_STRING_PATTERNS:
            sanitized = pattern.sub(replacement, sanitized)
        return sanitized

    return data


class SensitiveDataFilter(logging.Filter):
    """Logging filter that scrubs sensitive credentials from log records before formatting."""

    def filter(self, record: logging.LogRecord) -> bool:
        if record.args:
            if isinstance(record.args, dict):
                record.args = mask_sensitive_data(record.args)
            elif isinstance(record.args, (tuple, list)):
                record.args = tuple(mask_sensitive_data(arg) for arg in record.args)
        elif isinstance(record.msg, str):
            record.msg = mask_sensitive_data(record.msg)
        elif isinstance(record.msg, (dict, list)):
            record.msg = mask_sensitive_data(record.msg)

        return True


class JSONFormatter(logging.Formatter):
    """Formatter that outputs structured, machine-readable JSON log lines."""

    def format(self, record: logging.LogRecord) -> str:
        # Resolve request_id from record or context variable
        req_id = getattr(record, "request_id", None) or request_id_ctx.get()

        raw_message = record.getMessage()
        sanitized_message = mask_sensitive_data(raw_message)

        log_entry: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "level": record.levelname,
            "logger": record.name,
            "message": sanitized_message,
        }

        if req_id:
            log_entry["request_id"] = req_id

        # Standard extra attributes attached via logger.info(..., extra={...})
        standard_extras = [
            "method",
            "path",
            "status_code",
            "duration_ms",
            "client_ip",
            "user_id",
            "query_params",
        ]
        for key in standard_extras:
            val = getattr(record, key, None)
            if val is not None:
                log_entry[key] = mask_sensitive_data(val)

        # Include exception traceback if present
        if record.exc_info:
            log_entry["traceback"] = self.formatException(record.exc_info)

        return json.dumps(log_entry, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    """Returns a configured logger instance."""
    return logging.getLogger(name)


def setup_logging(level: str = "INFO") -> None:
    """Initializes root and application loggers with JSON formatting and data redaction."""
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers to avoid duplicated output
    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(JSONFormatter())
    stream_handler.addFilter(SensitiveDataFilter())

    root_logger.addHandler(stream_handler)
