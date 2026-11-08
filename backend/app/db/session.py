"""Database Engine, Session Factory, and Connectivity Checks."""

from collections.abc import Generator
from typing import Any

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    """Returns singleton SQLAlchemy Engine with Neon PgBouncer connection settings."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_recycle=240,
            pool_timeout=2.0,
        )
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    """Returns singleton sessionmaker bound to current engine."""
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=get_engine(),
        )
    return _session_factory


def get_db() -> Generator[Session, Any, None]:
    """FastAPI dependency yielding scoped database sessions."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
    finally:
        db.close()


def check_db_health(timeout: float = 2.0) -> bool:
    """Executes a lightweight ping (SELECT 1) to verify database connectivity.

    Raises OperationalError or other DB exceptions if connection fails or times out.
    """
    engine = get_engine()
    with engine.connect() as conn:
        conn.execution_options(timeout=timeout)
        conn.execute(text("SELECT 1"))
    return True
