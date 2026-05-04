"""E66 — Integration tests: procedural memory CRUD.

Tests the full procedural memory lifecycle: store → match → outcome → export.
"""

from collections.abc import Generator

import httpx
import pytest


class TestProceduralMemory:
    """Integration tests for procedural memory store, match, and outcome."""

    @pytest.fixture
    def client(
        self, base_url: str, default_headers: dict[str, str]
    ) -> Generator[httpx.Client, None, None]:
        with httpx.Client(base_url=base_url, headers=default_headers, timeout=30.0) as c:
            yield c

    def test_store_procedure_returns_201(self, client):
        """Storing a new procedure should return 201 with procedure_id."""
        resp = client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": "test-proc-agent",
                "name": "Send Email Workflow",
                "description": "Steps to compose and send an email to a user",
                "task_type": "email",
                "steps": [
                    {"action": "get_recipient", "params": {"field": "email"}},
                    {"action": "compose_body", "params": {"template": "default"}},
                    {"action": "send_email", "params": {"provider": "sendgrid"}},
                ],
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "procedure_id" in data
        assert data["name"] == "Send Email Workflow"
        assert data["task_type"] == "email"

    def test_match_procedure_by_similarity(self, client):
        """Matching should find semantically similar procedures."""
        # Store a procedure
        client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": "test-match-agent",
                "name": "Deploy to Production",
                "description": "Steps to deploy the application to AWS ECS production",
                "task_type": "devops",
                "steps": [
                    {"action": "run_tests"},
                    {"action": "build_docker_image"},
                    {"action": "push_to_ecr"},
                    {"action": "update_ecs_service"},
                ],
            },
        )

        # Match it
        resp = client.post(
            "/v1/memory/procedural/match",
            json={
                "agent_id": "test-match-agent",
                "task_description": "I need to deploy my app to production",
                "k": 3,
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["results"]) > 0
        assert data["results"][0]["name"] == "Deploy to Production"
        assert data["latency_ms"] > 0

    def test_outcome_updates_success_rate(self, client):
        """Reporting outcomes should update success/failure counts."""
        # Store
        store_resp = client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": "test-outcome-agent",
                "name": "Parse CSV",
                "description": "Parse a CSV file and extract structured data",
                "task_type": "data_processing",
                "steps": [{"action": "read_file"}, {"action": "parse_rows"}],
            },
        )
        proc_id = store_resp.json()["procedure_id"]

        # Report 3 successes
        for _ in range(3):
            resp = client.post(
                "/v1/memory/procedural/outcome",
                json={"procedure_id": proc_id, "success": True, "duration_ms": 150.0},
            )
            assert resp.status_code == 200

        # Report 1 failure
        resp = client.post(
            "/v1/memory/procedural/outcome",
            json={"procedure_id": proc_id, "success": False},
        )
        data = resp.json()
        assert data["success_count"] == 3
        assert data["failure_count"] == 1
        assert data["success_rate"] == 0.75

    def test_success_rate_weighting_in_match(self, client):
        """Procedures with higher success rates should rank higher."""
        agent = "test-weighting-agent"

        # Store two similar procedures
        r1 = client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": agent,
                "name": "Reliable File Upload",
                "description": "Upload a file to S3 with retries and validation",
                "task_type": "file_ops",
                "steps": [{"action": "validate"}, {"action": "upload"}, {"action": "verify"}],
            },
        )
        r2 = client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": agent,
                "name": "Basic File Upload",
                "description": "Simple file upload to S3 without validation",
                "task_type": "file_ops",
                "steps": [{"action": "upload"}],
            },
        )

        # Give #1 high success rate
        pid1 = r1.json()["procedure_id"]
        for _ in range(5):
            client.post(
                "/v1/memory/procedural/outcome", json={"procedure_id": pid1, "success": True}
            )

        # Give #2 low success rate
        pid2 = r2.json()["procedure_id"]
        for _ in range(5):
            client.post(
                "/v1/memory/procedural/outcome", json={"procedure_id": pid2, "success": False}
            )

        # Match — #1 should rank higher due to success rate
        match_resp = client.post(
            "/v1/memory/procedural/match",
            json={"agent_id": agent, "task_description": "upload a file to cloud storage", "k": 5},
        )
        results = match_resp.json()["results"]
        if len(results) >= 2:
            assert results[0]["procedure_id"] == pid1

    def test_export_includes_procedural(self, client):
        """Memory export should include procedural memories."""
        agent = "test-export-proc"

        # Store a procedure
        client.post(
            "/v1/memory/procedural/store",
            json={
                "agent_id": agent,
                "name": "Test Export Procedure",
                "description": "A procedure for testing export",
                "task_type": "test",
                "steps": [{"action": "test"}],
            },
        )

        # Export
        resp = client.get(f"/v1/admin/export/{agent}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agent_id"] == agent
        assert len(data["procedural"]) > 0
        assert data["total_memories"] > 0
        assert "exported_at" in data
