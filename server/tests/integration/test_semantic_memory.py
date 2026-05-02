"""E55 — Integration tests: store fact, contradiction resolution."""

import pytest
import httpx


class TestSemanticMemory:
    """Integration tests for semantic fact storage and contradiction resolution."""

    @pytest.fixture
    def client(self, base_url, default_headers):
        with httpx.Client(base_url=base_url, headers=default_headers, timeout=30.0) as c:
            yield c

    def test_store_fact_returns_201(self, client):
        """Storing a new fact should return 201 with fact_id."""
        resp = client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": "test-semantic",
                "subject": "user_alice",
                "predicate": "favorite_color",
                "object": "blue",
                "confidence": 0.9,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "fact_id" in data
        assert data["subject"] == "user_alice"
        assert data["predicate"] == "favorite_color"
        assert data["object"] == "blue"
        assert data["was_contradiction"] is False

    def test_query_facts_by_meaning(self, client):
        """Querying facts by natural language should return relevant facts."""
        # Store a fact first
        client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": "test-query-facts",
                "subject": "project_alpha",
                "predicate": "language",
                "object": "Rust",
            },
        )

        # Query by meaning
        resp = client.post(
            "/v1/memory/semantic/query",
            json={
                "agent_id": "test-query-facts",
                "query": "What programming language is project alpha using?",
                "k": 5,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) > 0

    def test_contradiction_detected_and_resolved(self, client):
        """Storing a conflicting fact should auto-resolve (higher confidence wins)."""
        agent = "test-contradiction"

        # Store initial fact with low confidence
        resp1 = client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "user_bob",
                "predicate": "city",
                "object": "New York",
                "confidence": 0.6,
            },
        )
        assert resp1.status_code == 201
        assert resp1.json()["was_contradiction"] is False

        # Store contradicting fact with higher confidence
        resp2 = client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "user_bob",
                "predicate": "city",
                "object": "San Francisco",
                "confidence": 0.9,
            },
        )
        assert resp2.status_code == 201
        data = resp2.json()
        assert data["was_contradiction"] is True
        assert data["replaced_fact_id"] is not None
        assert data["object"] == "San Francisco"

    def test_lower_confidence_does_not_replace(self, client):
        """A lower-confidence contradicting fact should not replace the existing one."""
        agent = "test-low-confidence"

        # Store with high confidence
        client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "user_carol",
                "predicate": "role",
                "object": "Engineer",
                "confidence": 0.95,
            },
        )

        # Try to override with lower confidence
        resp = client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "user_carol",
                "predicate": "role",
                "object": "Manager",
                "confidence": 0.3,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["was_contradiction"] is True
        # Lower confidence should NOT have replaced
        assert data["replaced_fact_id"] is None

    def test_same_fact_no_contradiction(self, client):
        """Re-storing the same fact (same SPO) should not flag as contradiction."""
        agent = "test-same-fact"

        client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "company",
                "predicate": "name",
                "object": "Kyros Inc",
            },
        )

        resp = client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent,
                "subject": "company",
                "predicate": "name",
                "object": "Kyros Inc",
            },
        )
        assert resp.status_code == 201
        assert resp.json()["was_contradiction"] is False
