"""FastAPI Application Main Entry Point."""

from datetime import UTC, datetime

from fastapi import FastAPI, Response, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.engine import create_engine

from app.core.config import get_settings


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Quiz Toán - Tin API",
        version="0.1.0",
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url=None,
    )

    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/healthz", status_code=status.HTTP_200_OK, tags=["System"])
    def healthz() -> dict:
        """Liveness probe: verifies process is alive without touching database."""
        return {"status": "ok", "app": "quiz-backend"}

    @app.get("/readyz", tags=["System"])
    def readyz(response: Response) -> dict:
        """Readiness probe: verifies database connection."""
        try:
            engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_timeout=2)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"status": "ready", "database": "connected"}
        except Exception as exc:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            response.headers["Retry-After"] = "2"
            return {"status": "unhealthy", "error": "db_unavailable", "detail": str(exc)}

    @app.get("/api/v1/time", tags=["System"])
    def server_time() -> dict:
        """Returns business server time in UTC ISO-8601 with Z and epoch milliseconds."""
        now = datetime.now(UTC)
        return {
            "server_now": now.isoformat().replace("+00:00", "Z"),
            "epoch_ms": int(now.timestamp() * 1000),
        }

    return app


app = create_app()
