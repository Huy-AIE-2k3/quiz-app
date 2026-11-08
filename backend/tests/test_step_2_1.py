"""Unit Tests for Step 2.1 — FastAPI Application Skeleton & Middlewares.

Covers:
- TC-2.1-01: Domain business error (AppError) returns correct status, JSON format, and X-Request-ID.
- TC-2.1-02: Unexpected 500 masks traceback/message, logs full stack, returns X-Request-ID.
- TC-2.1-03: DB disconnection triggers 503 db_unavailable with Retry-After; /healthz stays 200.
- TC-2.1-04: Body > 1 MB rejected with 413; file upload endpoint permits up to MAX_UPLOAD_MB.
- TC-2.1-05: CORS whitelist blocks untrusted origins, allows trusted with exposed X-Request-ID.
- TC-2.1-06: Sensitive credentials (passwords, tokens, Bearer auth) are redacted from logs.
- TC-2.1-07: Pydantic validation failure returns 422 validation_error with structured field details.
- Security Headers: Verifies nosniff, no-referrer, DENY, and no-store caching on /api endpoints.
"""

import io
import json
import logging
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.core.config import get_settings
from app.core.logging import JSONFormatter, SensitiveDataFilter
from app.main import create_app


@pytest.fixture(autouse=True)
def mock_env():
    """Sets standard mock environment variables for unit tests."""
    test_env = {
        "APP_ENV": "test",
        "DEBUG": "true",
        "DATABASE_URL": "postgresql://test:test@127.0.0.1:5432/test_db",
        "DATABASE_URL_DIRECT": "postgresql://test:test@127.0.0.1:5432/test_db",
        "SECRET_KEY": "test_secret_key_minimum_16_characters_long",
        "S3_ENDPOINT": "http://127.0.0.1:9000",
        "S3_BUCKET": "test-bucket",
        "S3_ACCESS_KEY": "test_access",
        "S3_SECRET_KEY": "test_secret",
        "CORS_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173",
        "MAX_UPLOAD_MB": "10",
    }
    with patch.dict(os.environ, test_env, clear=False):
        yield


@pytest.fixture
def client():
    """Provides a TestClient instance with test environment configured."""
    app = create_app()
    return TestClient(app)


def test_tc_2_1_01_business_error_handling(client):
    """TC-2.1-01: AppError returns explicit status, unified JSON structure, and X-Request-ID."""
    custom_request_id = "test-custom-req-id-12345"
    response = client.get(
        "/api/v1/dev/app-error",
        headers={"X-Request-ID": custom_request_id},
    )

    assert response.status_code == 409
    assert response.headers.get("X-Request-ID") == custom_request_id

    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "conflict_error"
    assert error["message"] == "Xung đột tài nguyên kiểm thử."
    assert error["details"] == {"conflict_key": "resource_123"}


def test_tc_2_1_02_unexpected_500_masks_internal_details():
    """TC-2.1-02: 500 error does NOT leak traceback or internal message, returns request ID."""
    app = create_app()
    # raise_server_exceptions=False allows testing server-generated 500 response
    test_client = TestClient(app, raise_server_exceptions=False)
    custom_request_id = "unhandled-req-999"
    response = test_client.get(
        "/api/v1/dev/boom",
        headers={"X-Request-ID": custom_request_id},
    )

    assert response.status_code == 500
    assert response.headers.get("X-Request-ID") == custom_request_id

    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "internal_error"
    assert "Đã xảy ra lỗi máy chủ nội bộ" in error["message"]
    assert error["details"] is None

    # Assert secret internal details and words "boom" are never exposed in response
    raw_body = response.text
    assert "boom" not in raw_body
    assert "database internal pointer" not in raw_body
    assert "Traceback" not in raw_body


def test_tc_2_1_03_db_unavailable_returns_503_retry_after(client):
    """TC-2.1-03: Database disconnection triggers 503 db_unavailable + Retry-After: 2."""
    # 1. /healthz remains 200 without touching DB
    health_resp = client.get("/healthz")
    assert health_resp.status_code == 200
    assert health_resp.json()["status"] == "ok"

    # 2. Endpoint encountering SQLAlchemy OperationalError
    db_err_resp = client.get("/api/v1/dev/db-error")
    assert db_err_resp.status_code == 503
    assert db_err_resp.headers.get("Retry-After") == "2"
    error = db_err_resp.json()["error"]
    assert error["code"] == "db_unavailable"
    assert "gián đoạn" in error["message"]

    # 3. /readyz returns 503 when connection fails
    with patch.dict(
        os.environ, {"DATABASE_URL": "postgresql://invalid:invalid@127.0.0.1:9999/none"}
    ):
        ready_resp = client.get("/readyz")
        assert ready_resp.status_code == 503
        assert ready_resp.headers.get("Retry-After") == "2"
        assert ready_resp.json()["status"] == "unhealthy"


def test_tc_2_1_04_body_size_limits(client):
    """TC-2.1-04: Body > 1 MB is rejected with 413; file upload route allows up to MAX_UPLOAD_MB."""
    # 1. POST JSON payload of ~1.2 MB to standard endpoint -> Must be rejected with 413
    oversized_data = {"name": "A" * (1_200_000), "count": 10}
    response = client.post("/api/v1/dev/echo", json=oversized_data)
    assert response.status_code == 413
    data = response.json()
    assert data["error"]["code"] == "request_entity_too_large"
    assert "1 MB" in data["error"]["message"]

    # 2. POST JSON payload of ~1.5 MB to upload endpoint -> Permitted under 10 MB limit
    upload_data = {"file_chunk": "B" * (1_500_000)}
    upload_resp = client.post("/api/v1/dev/upload", json=upload_data)
    assert upload_resp.status_code == 200
    assert upload_resp.json()["status"] == "uploaded"

    # 3. POST JSON payload of > 10 MB to upload endpoint -> Rejected with 413
    too_large_upload = {"file_chunk": "C" * (10_500_000)}
    too_large_resp = client.post("/api/v1/dev/upload", json=too_large_upload)
    assert too_large_resp.status_code == 413
    assert too_large_resp.json()["error"]["code"] == "request_entity_too_large"


def test_tc_2_1_05_cors_whitelist_enforcement(client):
    """TC-2.1-05: CORS origin filtering blocks untrusted origins, approves whitelisted origins."""
    settings = get_settings()
    allowed_origin = settings.cors_origin_list[0]
    untrusted_origin = "https://malicious-phishing-site.example.com"

    # 1. Preflight OPTIONS from untrusted origin
    blocked_preflight = client.options(
        "/api/v1/time",
        headers={
            "Origin": untrusted_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert "access-control-allow-origin" not in blocked_preflight.headers

    # 2. Preflight OPTIONS from trusted origin
    allowed_preflight = client.options(
        "/api/v1/time",
        headers={
            "Origin": allowed_origin,
            "Access-Control-Request-Method": "GET",
        },
    )
    assert allowed_preflight.headers.get("access-control-allow-origin") == allowed_origin

    # 3. Actual GET request from trusted origin receives exposed X-Request-ID header
    allowed_get = client.get(
        "/api/v1/time",
        headers={"Origin": allowed_origin},
    )
    assert allowed_get.status_code == 200
    assert allowed_get.headers.get("access-control-allow-origin") == allowed_origin
    assert "X-Request-ID" in allowed_get.headers.get("access-control-expose-headers", "")


def test_tc_2_1_06_sensitive_credentials_scrubbed_from_logs(client):
    """TC-2.1-06: Sensitive data (passwords, tokens, auth headers) never leak into logs."""
    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setFormatter(JSONFormatter())
    handler.addFilter(SensitiveDataFilter())

    target_logger = logging.getLogger("app.dev")
    target_logger.addHandler(handler)
    target_logger.setLevel(logging.INFO)

    secret_password = "S3cretPwd!"
    secret_token = "ultra_secret_bearer_token_xyz"

    try:
        response = client.post(
            "/api/v1/dev/login-test",
            json={"username": "student_01", "password": secret_password},
            headers={"Authorization": f"Bearer {secret_token}"},
        )
        assert response.status_code == 200

        logs = log_capture.getvalue()
        assert len(logs) > 0, "Log output should not be empty"

        # Assert plaintext secret password and bearer token are completely absent
        assert secret_password not in logs, "Plaintext password leaked in logs!"
        assert secret_token not in logs, "Plaintext bearer token leaked in logs!"
        assert "***" in logs, "Mask replacement '***' should be present in logs"

        # Verify output is valid JSON
        for line in logs.strip().split("\n"):
            parsed = json.loads(line)
            assert "timestamp" in parsed
            assert "level" in parsed
            assert "message" in parsed
    finally:
        target_logger.removeHandler(handler)


def test_tc_2_1_07_pydantic_validation_error_format(client):
    """TC-2.1-07: Invalid request body returns 422 validation_error with specific field errors."""
    # Sending missing 'count' and invalid 'name' (too short)
    response = client.post(
        "/api/v1/dev/echo",
        json={"name": "A"},  # min_length=2, missing 'count'
    )

    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    error = data["error"]
    assert error["code"] == "validation_error"
    assert "Dữ liệu yêu cầu không hợp lệ" in error["message"]

    details = error["details"]
    assert isinstance(details, list)
    assert len(details) >= 1

    fields = [d["field"] for d in details]
    assert "count" in fields or "name" in fields


def test_security_headers_and_cache_control(client):
    """SecurityHeadersMiddleware adds nosniff, no-referrer, DENY, and no-store for /api."""
    # 1. API endpoint
    api_resp = client.get("/api/v1/time")
    assert api_resp.status_code == 200
    assert api_resp.headers.get("X-Content-Type-Options") == "nosniff"
    assert api_resp.headers.get("Referrer-Policy") == "no-referrer"
    assert api_resp.headers.get("X-Frame-Options") == "DENY"
    assert "no-store" in api_resp.headers.get("Cache-Control", "")

    # 2. Response has generated X-Request-ID header
    assert "X-Request-ID" in api_resp.headers
    assert len(api_resp.headers["X-Request-ID"]) >= 16
