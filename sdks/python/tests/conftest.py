"""Pytest configuration and fixtures for Kyros SDK tests."""

import os
from typing import Generator

import pytest

from kyros import KyrosClient


@pytest.fixture
def api_key() -> str:
    """Get API key from environment or use test key."""
    return os.getenv("KYROS_API_KEY", "test-api-key")


@pytest.fixture
def base_url() -> str:
    """Get base URL from environment or use test URL."""
    return os.getenv("KYROS_BASE_URL", "http://localhost:8000")


@pytest.fixture
def client(api_key: str, base_url: str) -> Generator[KyrosClient, None, None]:
    """Create Kyros client for testing."""
    client = KyrosClient(api_key=api_key, base_url=base_url)
    yield client
    client.close()


@pytest.fixture
def agent_id() -> str:
    """Test agent ID."""
    return "test-agent-123"
