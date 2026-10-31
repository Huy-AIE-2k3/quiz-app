import logging
import time
import uuid
from datetime import UTC
from unittest.mock import patch

import pytest
from fastapi import APIRouter
from fastapi.testclient import TestClient
from freezegun import freeze_time
from pydantic import BaseModel, ValidationError

from app.core.config import Settings, get_settings
from app.core.errors import (
    AppError,
    AttemptClosed,
    DatabaseUnavailable,
    ExamNotOpen,
    Forbidden,
    InternalServerError,
    NotFound,
    RateLimited,
    Unauthorized,
    ValidationFailed,
)
from app.core.logging import JSONLogFormatter, user_id_ctx
from app.core.time import utcnow
from app.db.session import check_db_health, get_db
from app.main import app

# Create a dedicated testing router to test error handling & validation scenarios
scenario_router = APIRouter(prefix="/test-scenarios", tags=["Test"])


class SampleValidationModel(BaseModel):
    title: str
    duration_minutes: int
    score: float


@scenario_router.get("/error/attempt-closed")
def throw_attempt_closed():
    raise AttemptClosed("Phiên làm bài đã kết thúc")


@scenario_router.get("/error/custom-app-error")
def throw_custom_app_error():
    raise AppError(
        code="attempt_closed",
        message="Phiên làm bài đã kết thúc",
        status_code=409,
        details={"attempt_id": "test-uuid"},
    )


@scenario_router.get("/error/unauthorized")
def throw_unauthorized():
    raise Unauthorized()


@scenario_router.get("/error/forbidden")
def throw_forbidden():
    raise Forbidden()


@scenario_router.get("/error/not-found")
def throw_not_found():
    raise NotFound()


@scenario_router.get("/error/exam-not-open")
def throw_exam_not_open():
    raise ExamNotOpen()


@scenario_router.get("/error/rate-limited")
def throw_rate_limited():
    raise RateLimited()


@scenario_router.get("/error/validation-failed")
def throw_validation_failed():
    raise ValidationFailed()


@scenario_router.get("/error/internal-server")
def throw_internal_server():
    raise InternalServerError()


@scenario_router.get("/error/zero-division")
def throw_zero_division():
    return 1 / 0


@scenario_router.post("/validation-body")
def handle_validation_body(payload: SampleValidationModel):
    return {"status": "ok", "data": payload.model_dump()}


# Include test router into app once
app.include_router(scenario_router)

# Use raise_server_exceptions=False so 500 errors pass through the registered exception handler
client = TestClient(app, base_url="http://localhost:8000", raise_server_exceptions=False)


# ==============================================================================
# T1.2.1: GET /healthz (200 in < 50ms, no DB query)
# ==============================================================================
def test_t1_2_1_healthz_fast_no_db():
    with patch("app.main.check_db_health") as mock_db_check:
        start_time = time.perf_counter()
        response = client.get("/healthz")
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        # Assert response is fast (< 50ms) and succeeds
        assert response.status_code == 200
        assert elapsed_ms < 50.0

        # Assert no DB query was performed
        mock_db_check.assert_not_called()

        data = response.json()
        assert data["status"] == "healthy"
        assert data["app"] == "MATHRIX"
        assert "timestamp" in data
        assert "environment" in data


# ==============================================================================
# T1.2.2: GET /readyz when DB is down -> 503 + error.code = "db_unavailable"
# ==============================================================================
def test_t1_2_2_readyz_success_and_failure():
    # 1. Success case (DB is up)
    response_ok = client.get("/readyz")
    assert response_ok.status_code == 200
    assert response_ok.json() == {"status": "ready", "database": "connected"}

    # 2. Failure case (DB is down or disconnected)
    with patch("app.main.check_db_health", side_effect=DatabaseUnavailable("Mất kết nối database")):
        response_fail = client.get("/readyz")
        assert response_fail.status_code == 503
        data = response_fail.json()
        assert "error" in data
        assert data["error"]["code"] == "db_unavailable"
        assert data["error"]["message"] == "Mất kết nối database"


def test_check_db_health_function_catches_exception():
    """Verify check_db_health raises DatabaseUnavailable when engine connection fails."""
    with patch("app.db.session.engine.connect", side_effect=Exception("Connection refused")):
        with pytest.raises(DatabaseUnavailable) as exc_info:
            check_db_health()
        assert "Cơ sở dữ liệu không phản hồi" in str(exc_info.value)


# ==============================================================================
# T1.2.3: AppError("attempt_closed", 409) returns 409 and uniform JSON
# ==============================================================================
def test_t1_2_3_app_error_attempt_closed():
    # Subclass AttemptClosed
    response = client.get("/test-scenarios/error/attempt-closed")
    assert response.status_code == 409
    data = response.json()
    assert data == {
        "error": {
            "code": "attempt_closed",
            "message": "Phiên làm bài đã kết thúc",
        }
    }

    # Direct AppError instance with status 409 and details
    response_custom = client.get("/test-scenarios/error/custom-app-error")
    assert response_custom.status_code == 409
    assert response_custom.json() == {
        "error": {
            "code": "attempt_closed",
            "message": "Phiên làm bài đã kết thúc",
            "details": {"attempt_id": "test-uuid"},
        }
    }


def test_app_error_subclasses_coverage():
    """Verify other standard AppError subclasses conform to the uniform schema."""
    subclass_tests = [
        ("/test-scenarios/error/unauthorized", 401, "unauthorized"),
        ("/test-scenarios/error/forbidden", 403, "forbidden"),
        ("/test-scenarios/error/not-found", 404, "not_found"),
        ("/test-scenarios/error/exam-not-open", 403, "exam_not_open"),
        ("/test-scenarios/error/rate-limited", 429, "rate_limited"),
        ("/test-scenarios/error/validation-failed", 422, "validation_error"),
        ("/test-scenarios/error/internal-server", 500, "internal_error"),
    ]
    for endpoint, expected_status, expected_code in subclass_tests:
        res = client.get(endpoint)
        assert res.status_code == expected_status
        json_body = res.json()
        assert "error" in json_body
        assert json_body["error"]["code"] == expected_code


# ==============================================================================
# T1.2.4: Invalid body -> 422 validation_error with field list and friendly VN msg
# ==============================================================================
def test_t1_2_4_validation_error_vietnamese_message():
    # Send body with missing fields and invalid types
    bad_payload = {
        "title": "Toán giải tích",
        "duration_minutes": "not-an-integer",  # Invalid int
        # missing score
    }
    response = client.post("/test-scenarios/validation-body", json=bad_payload)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "validation_error"
    assert "Dữ liệu yêu cầu không hợp lệ" in data["error"]["message"]

    details = data["error"]["details"]
    assert isinstance(details, list)
    fields = [item["field"] for item in details]
    assert "duration_minutes" in fields
    assert "score" in fields

    # Check that friendly message explains the issue
    for item in details:
        assert isinstance(item["message"], str)
        assert len(item["message"]) > 0


# ==============================================================================
# T1.2.5: ZeroDivisionError -> 500 internal_error, no stack trace in response
# ==============================================================================
def test_t1_2_5_internal_error_hides_traceback(caplog):
    with caplog.at_level(logging.ERROR):
        response = client.get("/test-scenarios/error/zero-division")

        assert response.status_code == 500
        data = response.json()
        assert data == {
            "error": {
                "code": "internal_error",
                "message": "Đã xảy ra lỗi hệ thống nội bộ. Vui lòng thử lại sau.",
            }
        }
        # Verify stack trace is NEVER leaked to client
        raw_text = response.text
        assert "ZeroDivisionError" not in raw_text
        assert "Traceback" not in raw_text
        assert "division by zero" not in raw_text

        # Verify stack trace WAS logged internally
        log_text = caplog.text
        assert "Unhandled Exception" in log_text or "ZeroDivisionError" in log_text


# ==============================================================================
# T1.2.6: Untrusted CORS origin blocked
# ==============================================================================
def test_t1_2_6_cors_untrusted_origin_rejected():
    # 1. Untrusted origin
    untrusted_origin = "http://malicious-hacker-site.org"
    response_blocked = client.get("/healthz", headers={"Origin": untrusted_origin})
    assert response_blocked.status_code == 200
    # Starlette CORSMiddleware must NOT return allow-origin for untrusted origins
    assert response_blocked.headers.get("access-control-allow-origin") != untrusted_origin

    # 2. Trusted origin
    trusted_origin = "http://localhost:5173"
    response_allowed = client.get("/healthz", headers={"Origin": trusted_origin})
    assert response_allowed.status_code == 200
    assert response_allowed.headers.get("access-control-allow-origin") == trusted_origin


# ==============================================================================
# T1.2.7: utcnow() under freeze_time returns frozen UTC datetime with tzinfo
# ==============================================================================
def test_t1_2_7_utcnow_under_freeze_time():
    frozen_timestamp = "2026-10-31 08:30:00"
    with freeze_time(frozen_timestamp):
        current = utcnow()
        assert current.year == 2026
        assert current.month == 10
        assert current.day == 31
        assert current.hour == 8
        assert current.minute == 30
        assert current.second == 0
        assert current.tzinfo is not None
        assert current.tzinfo == UTC

    # Also test /time endpoint reflects utcnow()
    with freeze_time("2026-11-01 10:00:00"):
        res = client.get("/time")
        assert res.status_code == 200
        assert res.json()["utc"].startswith("2026-11-01T10:00:00")


# ==============================================================================
# T1.2.8: Every response has X-Request-ID; logger matches the same ID
# ==============================================================================
def test_t1_2_8_x_request_id_and_structured_log(caplog):
    # 1. Auto-generated UUID when not supplied
    res1 = client.get("/healthz")
    assert res1.status_code == 200
    req_id_1 = res1.headers.get("X-Request-ID")
    assert req_id_1 is not None
    # Validate UUID format
    uuid_obj = uuid.UUID(req_id_1)
    assert str(uuid_obj) == req_id_1

    # 2. Preserved custom X-Request-ID when provided by client
    custom_id = "test-client-trace-uuid-9999"
    with caplog.at_level(logging.INFO, logger="app.request"):
        res2 = client.get("/healthz", headers={"X-Request-ID": custom_id})
        assert res2.status_code == 200
        assert res2.headers.get("X-Request-ID") == custom_id

        # Verify logger recorded the exact same request_id
        matching_logs = [record for record in caplog.records if getattr(record, "request_id", None) == custom_id]
        assert len(matching_logs) > 0
        assert matching_logs[0].request_id == custom_id


# ==============================================================================
# T1.2.9: Missing or blank SECRET_KEY raises clear error on Settings() instantiation
# ==============================================================================
def test_t1_2_9_missing_secret_key_raises_error(monkeypatch):
    # Remove any SECRET_KEY from environment
    monkeypatch.delenv("SECRET_KEY", raising=False)

    # 1. Instantiation with empty string
    with pytest.raises((ValidationError, ValueError)) as exc_info_blank:
        Settings(SECRET_KEY="", _env_file=None)
    assert "SECRET_KEY" in str(exc_info_blank.value)

    # 2. Instantiation with whitespace only
    with pytest.raises((ValidationError, ValueError)) as exc_info_ws:
        Settings(SECRET_KEY="   ", _env_file=None)
    assert "SECRET_KEY" in str(exc_info_ws.value)

    # 3. Successful instantiation with a valid secret key
    valid_settings = Settings(SECRET_KEY="a-very-strong-and-valid-secret-key", _env_file=None)
    assert valid_settings.SECRET_KEY == "a-very-strong-and-valid-secret-key"


# ==============================================================================
# Additional Tests for 90%+ Coverage
# ==============================================================================
def test_settings_cors_parsing():
    """Test CORS_ORIGINS parser with string list, JSON list, comma separated list."""
    s1 = Settings(SECRET_KEY="secret-key-12345", CORS_ORIGINS="http://a.com, http://b.com", _env_file=None)
    assert s1.CORS_ORIGINS == ["http://a.com", "http://b.com"]

    s2 = Settings(
        SECRET_KEY="secret-key-12345",
        CORS_ORIGINS='["http://c.com", "http://d.com"]',
        _env_file=None,
    )
    assert s2.CORS_ORIGINS == ["http://c.com", "http://d.com"]

    s3 = Settings(SECRET_KEY="secret-key-12345", CORS_ORIGINS="", _env_file=None)
    assert s3.CORS_ORIGINS == []

    # Test get_settings() returns cached instance
    assert get_settings() is not None


def test_database_get_db_dependency():
    """Verify get_db dependency yields session and closes it."""
    db_gen = get_db()
    session = next(db_gen)
    assert session is not None
    with pytest.raises(StopIteration):
        next(db_gen)


def test_starlette_http_404_error_handler():
    """Verify unknown route returns uniform 404 JSON."""
    res = client.get("/this-route-does-not-exist-at-all")
    assert res.status_code == 404
    data = res.json()
    assert data["error"]["code"] == "not_found"


def test_api_v1_ping_and_root():
    """Verify /api/v1/ping and / endpoints."""
    res_ping = client.get("/api/v1/ping")
    assert res_ping.status_code == 200
    assert res_ping.json() == {"ping": "pong"}

    res_root = client.get("/")
    assert res_root.status_code == 200
    assert "MATHRIX" in res_root.json()["message"]


def test_json_log_formatter():
    """Verify JSONLogFormatter format with and without context variables."""
    formatter = JSONLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    user_id_ctx.set("user-uuid-1234")
    output = formatter.format(record)
    assert "user-uuid-1234" in output
    assert "Test log message" in output
