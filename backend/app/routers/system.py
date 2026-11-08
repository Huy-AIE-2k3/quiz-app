"""System Endpoints.

Health Check (/healthz), Readiness Check (/readyz), and Clock (/api/v1/time).
"""

import os

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.engine import create_engine

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.time import Clock, get_clock
from app.schemas.common import HealthResponse, ReadyResponse, ServerTimeResponse

logger = get_logger("app.system")
router = APIRouter(tags=["System"])


@router.get("/healthz", response_model=HealthResponse, status_code=status.HTTP_200_OK)
def healthz() -> dict:
    """Liveness probe: verifies web server process is responsive without touching database."""
    return {"status": "ok", "app": "quiz-backend"}


@router.get("/readyz", response_model=ReadyResponse)
def readyz(
    response: Response,
    clock: Clock = Depends(get_clock),
) -> dict:
    """Readiness probe: validates DB connectivity and monitors clock skew with Postgres."""
    settings = get_settings()
    db_url = os.environ.get("DATABASE_URL", settings.DATABASE_URL)
    try:
        engine = create_engine(db_url, pool_pre_ping=True, pool_timeout=2.0)
        with engine.connect() as conn:
            # Query current timestamp from database
            result = conn.execute(text("SELECT 1, clock_timestamp()")).first()
            if result and result[1]:
                db_now = result[1]
                app_now = clock.now()
                # Check clock skew between application server and database
                skew_seconds = abs((app_now - db_now).total_seconds())
                if skew_seconds > 2.0:
                    logger.warning(
                        "Cảnh báo lệch giờ giữa app server và database: %.3fs",
                        skew_seconds,
                        extra={"clock_skew_seconds": skew_seconds},
                    )

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
def server_time(clock: Clock = Depends(get_clock)) -> dict:
    """Authoritative business time endpoint.

    Returns UTC ISO-8601 timestamp ending in 'Z' and epoch milliseconds
    using Clock service for exam timer synchronization.
    """
    now = clock.now()
    return {
        "server_now": now.isoformat().replace("+00:00", "Z"),
        "epoch_ms": int(now.timestamp() * 1000),
    }
