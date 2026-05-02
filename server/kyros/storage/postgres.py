"""PostgreSQL async connection management with pgvector support."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.exc import SQLAlchemyError
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
    pool_recycle=1800,           # recycle connections every 30 min
    pool_timeout=30,             # raise after 30s waiting for a connection
    echo=settings.debug,
    connect_args={
        "command_timeout": 60,
        "timeout": 10,           # connection acquisition timeout
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
    except SQLAlchemyError:
        await session.rollback()
        raise
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
            raise ValueError(f"Invalid tenant_id: must be a valid UUID") from e
        
        # SET LOCAL does not support bound parameters in asyncpg
        # Safe to use f-string after UUID validation
        await session.execute(
            text(f"SET LOCAL kyros.current_tenant_id = '{tid}'")
        )
        yield session
        await session.commit()
    except SQLAlchemyError:
        await session.rollback()
        raise
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


async def run_migrations() -> None:
    """No-op — migrations must be run as a separate pre-deployment step.

    In production:
        alembic upgrade head

    Running migrations inside the app process is unsafe in multi-worker
    deployments because multiple workers could run migrations concurrently.
    """
    logger.debug("run_migrations() called — skipped (run 'alembic upgrade head' separately)")
