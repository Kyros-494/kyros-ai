"""Integration tests: authentication middleware.

Rate limiting has been removed from Kyros (open-source, self-hosted).
If you need request throttling, configure it at the reverse proxy level
(nginx, Caddy, Traefik, etc.).
"""

from __future__ import annotations

import pytest
import httpx


class TestAuthentication:
    """Verify that auth middleware correctly rejects invalid credentials."""

    @pytest.fixture
    def client(self, base_url):
        with httpx.Client(base_url=base_url, timeout=10.0) as c:
            yield c

    def test_missing_api_key_returns_401(self, client):
        """Request without X-API-Key header should return 401."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": "no-key", "query": "test", "k": 1},
        )
        assert resp.status_code == 401
        assert resp.json()["error"] == "missing_api_key"

    def test_invalid_api_key_returns_401(self, client):
        """Request with an unknown API key should return 401."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            headers={"X-API-Key": "mk_test_nonexistent_key_000000000000"},
            json={"agent_id": "bad-key", "query": "test", "k": 1},
        )
        assert resp.status_code == 401
        assert resp.json()["error"] == "invalid_api_key"

    def test_wrong_format_api_key_returns_401(self, client):
        """API key not starting with mk_live_ or mk_test_ should return 401."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            headers={"X-API-Key": "sk-1234567890abcdef"},
            json={"agent_id": "wrong-format", "query": "test", "k": 1},
        )
        assert resp.status_code == 401
        assert resp.json()["error"] == "invalid_api_key_format"

    def test_too_short_api_key_returns_401(self, client):
        """API key with suffix shorter than 16 chars should return 401."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            headers={"X-API-Key": "mk_test_short"},
            json={"agent_id": "short-key", "query": "test", "k": 1},
        )
        assert resp.status_code == 401

    def test_health_does_not_require_auth(self, client):
        """GET /health should work without any API key."""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_docs_does_not_require_auth(self, client):
        """GET /docs should work without any API key."""
        resp = client.get("/docs")
        assert resp.status_code == 200

    def test_valid_test_key_is_accepted(self, client, default_headers):
        """A valid mk_test_ key should be accepted in non-production."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            headers=default_headers,
            json={"agent_id": "auth-test-agent", "query": "test", "k": 1},
        )
        # Should be 200 (even if no results), not 401/403
        assert resp.status_code == 200
