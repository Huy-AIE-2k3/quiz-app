"""API Routers Package."""

from app.routers.admin import router as admin_router
from app.routers.auth import router as auth_router
from app.routers.student import router as student_router
from app.routers.system import router as system_router

__all__ = ["admin_router", "auth_router", "student_router", "system_router"]
