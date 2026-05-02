"""Alembic environment configuration for async PostgreSQL migrations."""

from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

# Import all models so Alembic can detect schema changes
from kyros.models import Base  # noqa: F401 — registers all ORM models

try:
    from kyros.config import get_settings
    _db_url = get_settings().database_url
except Exception as e:
    print(f"[alembic] ERROR: Could not load settings: {e}", file=sys.stderr)
    print("[alembic] Ensure KYROS_DATABASE_URL is set in your environment or .env file.", file=sys.stderr)
    sys.exit(1)

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url with the env-aware settings value.
# For offline mode (SQL generation), Alembic needs a sync-compatible URL —
# strip the +asyncpg driver so it can parse the DSN without the async driver.
_sync_db_url = _db_url.replace("postgresql+asyncpg://", "postgresql://")
config.set_main_option("sqlalchemy.url", _sync_db_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode — emit SQL to stdout without a DB connection."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Execute migrations within an open connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Create an async engine and run migrations."""
    # Use the original asyncpg URL for the async engine
    async_config = config.get_section(config.config_ini_section, {})
    async_config["sqlalchemy.url"] = _db_url  # restore +asyncpg for async engine
    connectable = async_engine_from_config(
        async_config,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    try:
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
    finally:
        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode — connect to DB directly."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
