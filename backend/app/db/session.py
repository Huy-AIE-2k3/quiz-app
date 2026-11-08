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
        connect_args: dict[str, Any] = {}
        if settings.DATABASE_URL.startswith("postgresql"):
            # Disable prepared statements for Neon PgBouncer transaction pooling
            connect_args["prepare_threshold"] = None

        engine_kwargs: dict[str, Any] = {
            "pool_pre_ping": True,
            "pool_recycle": 240,
            "pool_timeout": 5.0,
        }
        if not settings.DATABASE_URL.startswith("sqlite"):
            engine_kwargs["pool_size"] = 5
            engine_kwargs["max_overflow"] = 5

        if connect_args:
            engine_kwargs["connect_args"] = connect_args

        _engine = create_engine(settings.DATABASE_URL, **engine_kwargs)
    return _engine


def get_direct_engine() -> Engine:
    """Returns an engine bound directly without pooled limitations (for Alembic DDL migrations)."""
    settings = get_settings()
    url = settings.DATABASE_URL_DIRECT or settings.DATABASE_URL
    return create_engine(url, pool_pre_ping=True)


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
    """FastAPI dependency yielding scoped database sessions with automatic commit/rollback."""
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_engine() -> None:
    """Disposes and resets the singleton engine and session factory."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def check_db_health(timeout: float = 2.0) -> bool:
    """Executes a lightweight ping (SELECT 1) to verify database connectivity.

    Raises OperationalError or other DB exceptions if connection fails or times out.
    """
    engine = get_engine()
    with engine.connect() as conn:
        conn.execution_options(timeout=timeout)
        conn.execute(text("SELECT 1"))
    return True
