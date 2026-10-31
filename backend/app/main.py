from contextlib import asynccontextmanager
from typing import Any

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging
from app.core.middleware import RequestLoggingMiddleware
from app.core.time import utcnow
from app.db.session import check_db_health

settings = get_settings()

# Initialize structured JSON logging
setup_logging(log_level="DEBUG" if settings.DEBUG else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan context for startup and shutdown events."""
    # Startup verification
    yield
    # Shutdown cleanups


# Swagger documentation visibility control
# Disabled in production unless explicitly enabled via DOCS_ENABLED=True
docs_enabled = settings.DOCS_ENABLED and (
    settings.APP_ENV != "production" or settings.DOCS_ENABLED
)

app = FastAPI(
    title="MATHRIX Quiz Engine API",
    version="0.1.0",
    description="Backend REST API for MATHRIX - Online Assessment Platform for Mathematics & Computer Science",
    docs_url="/docs" if docs_enabled else None,
    redoc_url="/redoc" if docs_enabled else None,
    openapi_url="/openapi.json" if docs_enabled else None,
    lifespan=lifespan,
)

# 1. Unified Global Error Handlers (QUIZ.md §8.4)
register_error_handlers(app)

# 2. CORS Policy Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)

# 3. Request Tracing & Structured Logging Middleware
app.add_middleware(RequestLoggingMiddleware)

# ------------------------------------------------------------------------------
# System & Monitoring Endpoints (Unauthenticated, fast probes)
# ------------------------------------------------------------------------------


@app.get("/healthz", tags=["System"])
def health_check() -> dict[str, Any]:
    """
    Liveness probe for Render / K8s / UptimeRobot keep-alive.
    Crucial: Must respond under 50ms and NEVER query the database.
    """
    return {
        "status": "healthy",
        "app": "MATHRIX",
        "timestamp": utcnow().isoformat(),
        "environment": settings.APP_ENV,
    }


@app.get("/readyz", tags=["System"])
def readiness_check() -> dict[str, Any]:
    """
    Readiness probe for K8s / load balancers.
    Executes SELECT 1 against PostgreSQL. Returns 503 db_unavailable if down.
    """
    check_db_health()
    return {
        "status": "ready",
        "database": "connected",
    }


@app.get("/time", tags=["System"])
def get_current_time() -> dict[str, str]:
    """
    Returns the authoritative UTC ISO timestamp from core.time.utcnow().
    Used by clients to synchronize clocks for exam countdowns.
    """
    return {
        "utc": utcnow().isoformat(),
    }


@app.get("/", tags=["System"])
def root() -> dict[str, str]:
    return {
        "message": "Welcome to MATHRIX API Engine",
        "docs": "/docs" if docs_enabled else "disabled",
        "health": "/healthz",
    }


# ------------------------------------------------------------------------------
# API v1 Business Router
# ------------------------------------------------------------------------------
api_v1_router = APIRouter(prefix="/api/v1")


@api_v1_router.get("/ping", tags=["General"])
def ping() -> dict[str, str]:
    return {"ping": "pong"}


app.include_router(api_v1_router)
