from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="MATHRIX Quiz Engine API",
    version="0.1.0",
    description="Backend REST API for MATHRIX - Online Assessment Platform for Mathematics & Computer Science",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healthz", tags=["System"])
def health_check():
    """Health check endpoint for Render / UptimeRobot / Load balancer keep-alive."""
    return {
        "status": "healthy",
        "app": "MATHRIX",
        "timestamp": datetime.now(UTC).isoformat(),
        "environment": settings.APP_ENV,
    }


@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to MATHRIX API Engine",
        "docs": "/docs",
        "health": "/healthz",
    }
