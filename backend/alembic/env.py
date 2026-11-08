import os
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

import app.models  # noqa: F401
from alembic import context
from app.core.config import get_settings
from app.db.base import Base

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def get_direct_url() -> str:
    """Returns direct database URL prioritizing DATABASE_URL_DIRECT."""
    # Check OS environment first, then application settings
    direct_url = os.environ.get("DATABASE_URL_DIRECT")
    if direct_url:
        return direct_url
    try:
        settings = get_settings()
        if settings.DATABASE_URL_DIRECT:
            return settings.DATABASE_URL_DIRECT
        if settings.DATABASE_URL:
            return settings.DATABASE_URL
    except Exception:
        pass
    return os.environ.get(
        "DATABASE_URL", "postgresql://quiz_user:test_password_only@127.0.0.1:5432/quiz_dev"
    )


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_direct_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    url = get_direct_url()
    connectable = create_engine(
        url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
