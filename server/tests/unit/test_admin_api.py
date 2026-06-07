"""Unit tests for new Admin API endpoints (/agents and /tenants)."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
import pytest
from kyros.main import app

client = TestClient(app)


def test_list_agents_unauthenticated() -> None:
    """GET /v1/admin/agents must reject requests without an API key."""
    response = client.get("/v1/admin/agents")
    assert response.status_code == 401


@patch("kyros.middleware.auth.get_db_session")
@patch("kyros.api.v1.admin.get_db_session_for_tenant")
def test_list_agents_success(mock_get_session_tenant: MagicMock, mock_get_session: MagicMock) -> None:
    """GET /v1/admin/agents returns a list of agents for a valid tenant."""
    # Set mock properties on app state to satisfy dependency resolution
    app.state.embedder = MagicMock()
    app.state.redis = AsyncMock()

    # 1. Mock authentication database check
    mock_db = AsyncMock()
    mock_tenant = MagicMock()
    mock_tenant.id = uuid.uuid4()
    mock_tenant.plan = "pro"
    mock_tenant.is_active = True
    
    mock_auth_result = MagicMock()
    mock_auth_result.fetchone.return_value = mock_tenant
    mock_db.execute.return_value = mock_auth_result

    # 2. Mock list_agents database query
    mock_tenant_db = AsyncMock()
    mock_agent = MagicMock()
    mock_agent.external_id = "agent-123"
    mock_agent.display_name = "My Test Agent"
    mock_agent.metadata = {"key": "value"}
    
    mock_agent_result = MagicMock()
    mock_agent_result.fetchall.return_value = [mock_agent]
    mock_tenant_db.execute.return_value = mock_agent_result

    # Set up mock context managers
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc, tb):
            pass

    class AsyncContextManagerTenantMock:
        async def __aenter__(self):
            return mock_tenant_db
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_get_session.return_value = AsyncContextManagerMock()
    mock_get_session_tenant.return_value = AsyncContextManagerTenantMock()

    # Make request
    headers = {"X-API-Key": "mk_live_some_valid_secret_key_123456"}
    response = client.get("/v1/admin/agents", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) == 1
    assert data["agents"][0]["agent_id"] == "agent-123"
    assert data["agents"][0]["display_name"] == "My Test Agent"


@patch("kyros.config.get_settings")
@patch("kyros.storage.postgres.get_db_session")
def test_create_tenant_success(mock_get_session: MagicMock, mock_settings: MagicMock) -> None:
    """POST /v1/admin/tenants creates a tenant and returns an API key when authenticated."""
    # Set up mock admin token
    mock_settings.return_value.admin_token = "admin-secret-token"
    mock_settings.return_value.jwt_secret_key = "jwt-secret-token"

    mock_db = AsyncMock()
    
    class AsyncContextManagerMock:
        async def __aenter__(self):
            return mock_db
        async def __aexit__(self, exc_type, exc, tb):
            pass

    mock_get_session.return_value = AsyncContextManagerMock()

    # Make request
    headers = {"X-Admin-Token": "admin-secret-token"}
    payload = {"name": "New Pilot Tenant", "email": "pilot@kyros.dev"}
    response = client.post("/v1/admin/tenants", json=payload, headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "New Pilot Tenant"
    assert data["email"] == "pilot@kyros.dev"
    assert "api_key" in data
    assert data["api_key"].startswith("mk_live_")
    assert "tenant_id" in data
