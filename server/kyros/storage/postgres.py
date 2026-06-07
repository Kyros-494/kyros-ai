"""PostgreSQL async connection management with pgvector support."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from kyros.config import get_settings
from kyros.logging import get_logger

logger = get_logger("kyros.storage.postgres")
settings = get_settings()

engine = create_async_engine(
    settings.database_url,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    # pool_pre_ping adds a round-trip on every checkout — disabled in favour of
    # pool_recycle which handles stale connections without the per-request cost.
    pool_pre_ping=False,
    pool_recycle=1800,  # recycle connections every 30 min
    pool_timeout=30,  # raise after 30s waiting for a connection
    echo=settings.debug,
    connect_args={
        "command_timeout": 60,
        "timeout": 10,  # connection acquisition timeout
    },
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Register pgvector type codec on every new connection so Python lists
# are automatically serialized/deserialized as PostgreSQL vector columns.
@event.listens_for(engine.sync_engine, "connect")
def _register_pgvector(dbapi_connection, connection_record) -> None:
    from pgvector.asyncpg import register_vector

    dbapi_connection.run_async(lambda conn: register_vector(conn))


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional async session.

    Commits on clean exit, rolls back on any exception, always closes.
    """
    session = async_session_factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


@asynccontextmanager
async def get_db_session_for_tenant(tenant_id: str) -> AsyncGenerator[AsyncSession, None]:
    """Provide a transactional session with RLS tenant context set.

    Sets the PostgreSQL session variable kyros.current_tenant_id so that
    Row-Level Security policies allow access to the correct tenant's rows.

    Usage:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            ...
    """
    from uuid import UUID

    session = async_session_factory()
    try:
        # Validate tenant_id is a valid UUID to prevent SQL injection
        try:
            validated_uuid = UUID(str(tenant_id))
            tid = str(validated_uuid)
        except (ValueError, AttributeError) as e:
            logger.error("Invalid tenant_id format", tenant_id=tenant_id, error=str(e))
            raise ValueError("Invalid tenant_id: must be a valid UUID") from e

        # SET LOCAL does not support bound parameters in asyncpg
        # Safe to use f-string after UUID validation
        await session.execute(text(f"SET LOCAL kyros.current_tenant_id = '{tid}'"))
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def run_migrations() -> None:
    """Run database migrations using Alembic programmatically via a subprocess.

    This ensures migrations are applied automatically in development and test environments
    without risking async event loop issues.
    """
    import subprocess
    import sys

    logger.info("Running database migrations via Alembic...")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True,
            text=True,
            check=True,
        )
        logger.info("Database migrations completed successfully", stdout=result.stdout)
    except subprocess.CalledProcessError as e:
        logger.error("Database migrations failed", stderr=e.stderr, stdout=e.stdout)
        raise RuntimeError(f"Database migrations failed: {e.stderr}") from e


async def bootstrap_default_tenant(api_key: str) -> None:
    """Hash the provided API key and seed a default tenant if it doesn't already exist.

    Uses a stable tenant ID to make local development and SDK integrations reproducible.
    """
    import hashlib
    import uuid

    if not api_key:
        logger.info("No default API key set. Skipping default tenant auto-bootstrap.")
        return

    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    safe_prefix = api_key[:16] + "..." if len(api_key) > 16 else api_key[:8] + "..."
    logger.info("Checking for default tenant bootstrap...", key_prefix=safe_prefix)

    default_tenant_id = uuid.UUID("00000000-0000-0000-0000-000000000000")

    try:
        async with get_db_session() as session:
            result = await session.execute(
                text("SELECT id FROM tenants WHERE api_key_hash = :key_hash OR id = :id"),
                {"key_hash": key_hash, "id": default_tenant_id},
            )
            row = result.fetchone()
            if not row:
                await session.execute(
                    text("""
                    INSERT INTO tenants (
                        id, name, email, api_key_hash, plan, is_active, created_at, updated_at
                    )
                    VALUES (
                        :id,
                        'Default Tenant',
                        'admin@kyros.dev',
                        :key_hash,
                        'pro',
                        true,
                        NOW(),
                        NOW()
                    )
                    """),
                    {"id": default_tenant_id, "key_hash": key_hash},
                )
                logger.info(
                    "Successfully bootstrapped default tenant",
                    tenant_id=str(default_tenant_id),
                )
            else:
                logger.info("Default tenant already exists. Bootstrapping skipped.")
    except Exception as e:
        logger.error("Failed to bootstrap default tenant", error=str(e))
