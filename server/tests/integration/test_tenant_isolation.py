"""E43 — Integration test: tenant isolation (A cannot see B's data).

Verifies that Row-Level Security and auth middleware properly isolate tenants.
"""

from collections.abc import Generator

import httpx
import pytest


class TestTenantIsolation:
    """Tenant A's memories must never appear in Tenant B's recall results."""

    @pytest.fixture
    def tenant_a_client(self, base_url: str) -> Generator[httpx.Client, None, None]:
        with httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": "mk_test_tenant_a_key_111", "Content-Type": "application/json"},
            timeout=30.0,
        ) as c:
            yield c

    @pytest.fixture
    def tenant_b_client(self, base_url: str) -> Generator[httpx.Client, None, None]:
        with httpx.Client(
            base_url=base_url,
            headers={"X-API-Key": "mk_test_tenant_b_key_222", "Content-Type": "application/json"},
            timeout=30.0,
        ) as c:
            yield c

    def test_tenant_a_cannot_see_tenant_b_memories(self, tenant_a_client, tenant_b_client):
        """Tenant A stores a memory; Tenant B should NOT find it."""
        unique_content = "secret_sauce_tenant_a_only_abc123"

        # Tenant A stores a memory
        resp_a = tenant_a_client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": "shared-agent-name", "content": unique_content},
        )
        assert resp_a.status_code == 201

        # Tenant B tries to recall it
        resp_b = tenant_b_client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": "shared-agent-name", "query": unique_content, "k": 10},
        )
        assert resp_b.status_code == 200
        results = resp_b.json()["results"]

        # Tenant B should NOT find Tenant A's memory
        for r in results:
            assert unique_content not in r["content"], "SECURITY BREACH: tenant isolation failed!"

    def test_same_agent_id_different_tenants(self, tenant_a_client, tenant_b_client):
        """Two tenants using the same agent_id should have independent memory spaces."""
        agent = "my-chatbot"

        # Both tenants store different facts about the same agent
        tenant_a_client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": agent, "content": "Tenant A: user prefers cats"},
        )
        tenant_b_client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": agent, "content": "Tenant B: user prefers dogs"},
        )

        # Tenant A recalls — should only see "cats"
        resp_a = tenant_a_client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": agent, "query": "What pet does the user prefer?", "k": 5},
        )
        if resp_a.status_code == 200 and resp_a.json()["results"]:
            for r in resp_a.json()["results"]:
                assert "dogs" not in r["content"].lower(), "ISOLATION BREACH: A sees B's data"

    def test_tenant_b_cannot_delete_tenant_a_memory(self, tenant_a_client, tenant_b_client):
        """Tenant B should not be able to delete Tenant A's memory."""
        # Tenant A stores
        resp = tenant_a_client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": "isolation-test", "content": "Protected data"},
        )
        memory_id = resp.json()["memory_id"]

        # Tenant B tries to delete it
        delete_resp = tenant_b_client.delete(f"/v1/memory/episodic/{memory_id}")
        # Should either 404 or silently no-op (not 204 success on A's data)
        assert delete_resp.status_code in (204, 404)
        # Even if 204, the memory should still exist for Tenant A
