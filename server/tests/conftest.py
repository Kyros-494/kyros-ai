"""Shared pytest fixtures for integration and unit tests."""

from __future__ import annotations

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from sqlalchemy import text

# Ensure the server package is importable when running tests directly
_server_root = str(Path(__file__).parent.parent)
if _server_root not in sys.path:
    sys.path.insert(0, _server_root)

# Ensure required settings exist even when .env is not present in CI/local test runs.
os.environ.setdefault("KYROS_DATABASE_URL", "postgresql+asyncpg://kyros:test@localhost:5432/kyros_test")
os.environ.setdefault("KYROS_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("KYROS_JWT_SECRET_KEY", "ci-test-secret-key-minimum-32-chars")

from kyros.storage.postgres import get_db_session


class SessionAdapter:
    """Compat wrapper: transparently wraps raw SQL strings in text() so tests
    can use plain strings without importing sqlalchemy in every test file."""

    def __init__(self, session) -> None:
        self._session = session

    async def execute(self, statement, *args, **kwargs):
        if isinstance(statement, str):
            statement = text(statement)
        return await self._session.execute(statement, *args, **kwargs)

    async def scalar(self, statement, *args, **kwargs):
        if isinstance(statement, str):
            statement = text(statement)
        return await self._session.scalar(statement, *args, **kwargs)

    def __getattr__(self, item):
        return getattr(self._session, item)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[SessionAdapter, None]:
    """Provide a transactional async DB session for tests.

    The session is rolled back after each test so tests are isolated
    and do not leave data in the database.
    """
    async with get_db_session() as session:
        yield SessionAdapter(session)


@pytest.fixture(scope="session")
def base_url() -> str:
    """Base URL for the running server (override with KYROS_TEST_URL env var)."""
    return os.environ.get("KYROS_TEST_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def test_api_key() -> str:
    """API key used for integration tests (override with KYROS_TEST_API_KEY)."""
    return os.environ.get("KYROS_TEST_API_KEY", "mk_test_integration_test_key_12345")


@pytest.fixture(scope="session")
def default_headers(test_api_key: str) -> dict[str, str]:
    """Default headers for all HTTP integration test requests."""
    return {"X-API-Key": test_api_key, "Content-Type": "application/json"}
