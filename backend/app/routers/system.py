"""System Endpoints: Health Check (/healthz), Readiness Check (/readyz), and Clock (/api/v1/time).
"""

import os
from datetime import UTC, datetime

from fastapi import APIRouter, Response, status
from sqlalchemy import text
from sqlalchemy.engine import create_engine

from app.core.config import get_settings
from app.schemas.common import HealthResponse, ReadyResponse, ServerTimeResponse

router = APIRouter(tags=["System"])


@router.get("/healthz", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def healthz() -> dict:
    """Liveness probe: verifies web server process is responsive without touching database.

    Used by infrastructure ping services to keep free hosting active.
    """
    return {"status": "ok", "app": "quiz-backend"}


@router.get("/readyz", response_model=ReadyResponse)
def readyz(response: Response) -> dict:
    """Readiness probe: validates database connectivity with a 2-second timeout.

    Returns 503 with Retry-After header if Neon database is sleeping or unreachable.
    """
    settings = get_settings()
    db_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    try:
        engine = create_engine(db_url, pool_pre_ping=True, pool_timeout=2.0)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        response.headers["Retry-After"] = "2"
        return {
            "status": "unhealthy",
            "error": "db_unavailable",
            "detail": "Dịch vụ cơ sở dữ liệu tạm thời gián đoạn.",
        }


@router.get("/api/v1/time", response_model=ServerTimeResponse)
def server_time() -> dict:
    """Authoritative business time endpoint.

    Returns UTC ISO-8601 timestamp ending in 'Z' and epoch milliseconds
    for exam timer synchronization.
    """
    now = datetime.now(UTC)
    return {
        "server_now": now.isoformat().replace("+00:00", "Z"),
        "epoch_ms": int(now.timestamp() * 1000),
    }
