"""Tests for Kyros Python SDK Client."""

from __future__ import annotations

import pytest

from kyros import KyrosClient
from kyros.exceptions import KyrosAPIError, KyrosConnectionError


def test_client_initialization() -> None:
    """Test client can be initialized."""
    client = KyrosClient(api_key="test-key", base_url="http://localhost:8000")
    assert client.base_url == "http://localhost:8000"
    assert client.headers["X-API-Key"] == "test-key"


def test_client_strips_trailing_slash() -> None:
    """Test client strips trailing slash from base URL."""
    client = KyrosClient(api_key="test-key", base_url="http://localhost:8000/")
    assert client.base_url == "http://localhost:8000"


def test_remember_requires_server() -> None:
    """Test remember raises connection error without server."""
    client = KyrosClient(api_key="test-key", base_url="http://localhost:9999")
    with pytest.raises(KyrosConnectionError):
        client.remember(agent_id="test", content="test content")


def test_recall_requires_server() -> None:
    """Test recall raises connection error without server."""
    client = KyrosClient(api_key="test-key", base_url="http://localhost:9999")
    with pytest.raises(KyrosConnectionError):
        client.recall(agent_id="test", query="test query")


def test_health_requires_server() -> None:
    """Test health raises connection error without server."""
    client = KyrosClient(api_key="test-key", base_url="http://localhost:9999")
    with pytest.raises(KyrosConnectionError):
        client.health()
