"""Tests for Health & Readiness Endpoints and Fail-Fast Settings."""

import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings


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
    }
    with patch.dict(os.environ, test_env, clear=False):
        yield


def test_tc_0_1_01_healthz_endpoint():
    """TC-0.1-01: Health check endpoint returns 200 without touching database."""
    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_server_time_endpoint():
    """Endpoint /api/v1/time returns server UTC time with Z and epoch milliseconds."""
    from app.main import create_app

    client = TestClient(create_app())
    response = client.get("/api/v1/time")
    assert response.status_code == 200
    data = response.json()
    assert "server_now" in data
    assert data["server_now"].endswith("Z")
    assert "epoch_ms" in data
    assert isinstance(data["epoch_ms"], int)


def test_tc_0_1_02_missing_environment_variable():
    """TC-0.1-02: Missing required environment variables triggers fail-fast validation error."""
    # When DATABASE_URL is missing
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValidationError) as exc_info:
            Settings(_env_file=None)  # pyright: ignore

        errors = exc_info.value.errors()
        missing_fields = {e["loc"][0] for e in errors}
        assert "DATABASE_URL" in missing_fields
        assert "SECRET_KEY" in missing_fields


def test_tc_0_1_05_readyz_fails_when_db_down():
    """TC-0.1-05: /readyz returns 503 when DB down, while /healthz returns 200."""
    from app.main import create_app

    client = TestClient(create_app())

    # /healthz is 200
    health_resp = client.get("/healthz")
    assert health_resp.status_code == 200

    # /readyz with unreachable database returns 503
    with patch.dict(os.environ, {"DATABASE_URL": "postgresql://invalid:invalid@127.0.0.1:9999/none"}):
        ready_resp = client.get("/readyz")
        assert ready_resp.status_code == 503
        assert ready_resp.headers.get("Retry-After") == "2"
        assert ready_resp.json()["status"] == "unhealthy"
