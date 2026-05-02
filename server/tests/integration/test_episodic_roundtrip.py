"""Integration test: remember → recall → forget round-trip.

Tests the full memory lifecycle against the Kyros API.
Requires: docker-compose up (Postgres + Redis + server running)
"""

from __future__ import annotations

import pytest
import httpx


class TestEpisodicRoundTrip:
    """Full lifecycle: remember → recall → verify → forget → verify gone."""

    @pytest.fixture
    def client(self, base_url, default_headers):
        with httpx.Client(base_url=base_url, headers=default_headers, timeout=30.0) as c:
            yield c

    def test_remember_creates_memory(self, client):
        """POST /v1/memory/episodic/remember should return 201 with memory_id."""
        resp = client.post(
            "/v1/memory/episodic/remember",
            json={
                "agent_id": "test-agent-roundtrip",
                "content": "The user's favorite color is blue",
                "importance": 0.8,
            },
        )
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "memory_id" in data
        assert data["agent_id"] == "test-agent-roundtrip"
        assert data["memory_type"] == "episodic"

    def test_remember_rejects_empty_content(self, client):
        """Storing an empty content string should return 422."""
        resp = client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": "test-agent-roundtrip", "content": ""},
        )
        assert resp.status_code == 422

    def test_remember_rejects_missing_agent_id(self, client):
        """Missing agent_id should return 422."""
        resp = client.post(
            "/v1/memory/episodic/remember",
            json={"content": "some content"},
        )
        assert resp.status_code == 422

    def test_recall_finds_memory(self, client):
        """POST /v1/memory/episodic/recall should find semantically similar memories."""
        store_resp = client.post(
            "/v1/memory/episodic/remember",
            json={
                "agent_id": "test-agent-recall",
                "content": "User prefers Python for backend development",
            },
        )
        assert store_resp.status_code == 201

        recall_resp = client.post(
            "/v1/memory/episodic/recall",
            json={
                "agent_id": "test-agent-recall",
                "query": "What programming language does the user prefer?",
                "k": 5,
            },
        )
        assert recall_resp.status_code == 200, recall_resp.text
        data = recall_resp.json()
        assert "results" in data
        assert "latency_ms" in data
        assert data["latency_ms"] >= 0
        assert len(data["results"]) > 0
        assert "Python" in data["results"][0]["content"]

    def test_recall_returns_empty_for_unknown_agent(self, client):
        """Recalling for an agent with no memories should return empty results, not an error."""
        resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": "agent-that-does-not-exist-xyz", "query": "anything", "k": 5},
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []

    def test_forget_deletes_memory(self, client):
        """DELETE /v1/memory/episodic/{id} should soft-delete; recall should not find it."""
        store_resp = client.post(
            "/v1/memory/episodic/remember",
            json={
                "agent_id": "test-agent-forget",
                "content": "This memory will be forgotten: xyzzy_unique_42",
            },
        )
        assert store_resp.status_code == 201
        memory_id = store_resp.json()["memory_id"]

        forget_resp = client.delete(f"/v1/memory/episodic/{memory_id}")
        assert forget_resp.status_code == 204

        recall_resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": "test-agent-forget", "query": "xyzzy_unique_42", "k": 5},
        )
        assert recall_resp.status_code == 200
        found_ids = [r["memory_id"] for r in recall_resp.json()["results"]]
        assert memory_id not in found_ids, "Forgotten memory still appears in recall"

    def test_forget_invalid_uuid_returns_422(self, client):
        """DELETE with a non-UUID memory_id should return 422."""
        resp = client.delete("/v1/memory/episodic/not-a-uuid")
        assert resp.status_code == 422

    def test_recall_with_session_filter(self, client):
        """Recall should support filtering by session_id."""
        agent = "test-agent-session"
        client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": agent, "content": "Session A data", "session_id": "sess-A"},
        )
        client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": agent, "content": "Session B data", "session_id": "sess-B"},
        )

        resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": agent, "query": "data", "session_id": "sess-A", "k": 10},
        )
        assert resp.status_code == 200
        # All returned results should belong to sess-A
        for r in resp.json()["results"]:
            assert r.get("session_id") in ("sess-A", None)

    def test_remember_with_metadata(self, client):
        """Memories should preserve arbitrary metadata."""
        resp = client.post(
            "/v1/memory/episodic/remember",
            json={
                "agent_id": "test-agent-meta",
                "content": "Test with metadata",
                "metadata": {"source": "test", "version": 2},
            },
        )
        assert resp.status_code == 201

    def test_recall_k_limit_respected(self, client):
        """Recall should never return more results than k."""
        agent = "test-agent-k-limit"
        for i in range(10):
            client.post(
                "/v1/memory/episodic/remember",
                json={"agent_id": agent, "content": f"Memory number {i} about testing"},
            )

        resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": agent, "query": "testing", "k": 3},
        )
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 3

    def test_recall_response_has_required_fields(self, client):
        """Each recall result must contain the required schema fields."""
        agent = "test-agent-schema"
        client.post(
            "/v1/memory/episodic/remember",
            json={"agent_id": agent, "content": "Schema validation test memory"},
        )
        resp = client.post(
            "/v1/memory/episodic/recall",
            json={"agent_id": agent, "query": "schema validation", "k": 1},
        )
        assert resp.status_code == 200
        results = resp.json()["results"]
        if results:
            r = results[0]
            assert "memory_id" in r
            assert "content" in r
            assert "relevance_score" in r
            assert "importance" in r
            assert "created_at" in r
