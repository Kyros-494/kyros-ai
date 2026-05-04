"""Load test with Locust.

Simulates realistic traffic patterns against a running Kyros server.

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Or headless (CI):
    locust -f tests/load/locustfile.py --host=http://localhost:8000 \
           --users=50 --spawn-rate=5 --run-time=60s --headless
"""

from __future__ import annotations

import os
import random
from typing import Any

from locust import HttpUser, between, events, task

# API key for load testing — override with KYROS_LOAD_TEST_KEY env var
_API_KEY = os.environ.get("KYROS_LOAD_TEST_KEY", "mk_test_loadtest_key_001")
_HEADERS = {"X-API-Key": _API_KEY, "Content-Type": "application/json"}

# Agents to spread load across (simulates multiple tenants)
_AGENTS = [f"load-agent-{i:03d}" for i in range(10)]

# Sample content pool for realistic variety
_CONTENT_POOL = [
    "User prefers dark mode in all applications",
    "The project deadline is end of Q2",
    "User is allergic to peanuts — critical dietary restriction",
    "Preferred programming language is Python for backend",
    "User lives in San Francisco, timezone UTC-8",
    "Meeting scheduled for Monday at 10am with the design team",
    "Budget approved for cloud infrastructure: $5,000/month",
    "User's email is user@example.com",
    "The API rate limit is 1000 requests per minute on Pro plan",
    "User prefers concise responses without unnecessary preamble",
]

_QUERIES = [
    "What are the user's preferences?",
    "What is the project deadline?",
    "Any dietary restrictions I should know about?",
    "What programming language does the user prefer?",
    "When is the next meeting?",
    "What is the budget?",
]


@events.test_start.add_listener
def on_test_start(environment: Any, **kwargs: Any) -> None:
    print(f"[Locust] Load test starting against {environment.host}")
    print(f"[Locust] Using API key: {_API_KEY[:20]}...")


@events.test_stop.add_listener
def on_test_stop(environment: Any, **kwargs: Any) -> None:
    stats = environment.stats.total
    print("\n[Locust] Test complete.")
    print(f"  Requests:  {stats.num_requests}")
    print(f"  Failures:  {stats.num_failures}")
    print(f"  Avg (ms):  {stats.avg_response_time:.1f}")
    print(f"  P95 (ms):  {stats.get_response_time_percentile(0.95):.1f}")
    print(f"  RPS:       {stats.current_rps:.1f}")


class KyrosUser(HttpUser):
    """Simulates a realistic AI agent workload."""

    wait_time = between(0.01, 0.05)

    def on_start(self) -> None:
        """Pick a random agent for this virtual user."""
        self.agent_id = random.choice(_AGENTS)

    @task(35)
    def remember(self) -> None:
        """Store an episodic memory."""
        self.client.post(
            "/v1/memory/episodic/remember",
            json={
                "agent_id": self.agent_id,
                "content": random.choice(_CONTENT_POOL),
                "importance": round(random.uniform(0.3, 0.9), 2),
            },
            headers=_HEADERS,
            name="/v1/memory/episodic/remember",
        )

    @task(35)
    def recall(self) -> None:
        """Recall relevant memories."""
        self.client.post(
            "/v1/memory/episodic/recall",
            json={
                "agent_id": self.agent_id,
                "query": random.choice(_QUERIES),
                "k": 5,
            },
            headers=_HEADERS,
            name="/v1/memory/episodic/recall",
        )

    @task(10)
    def store_fact(self) -> None:
        """Store a semantic fact."""
        subjects = ["user", "project", "company", "system"]
        predicates = ["prefers", "uses", "requires", "has"]
        objects = ["Python", "dark mode", "fast responses", "PostgreSQL"]
        self.client.post(
            "/v1/memory/semantic/facts",
            json={
                "agent_id": self.agent_id,
                "subject": random.choice(subjects),
                "predicate": random.choice(predicates),
                "object": random.choice(objects),
                "confidence": round(random.uniform(0.7, 1.0), 2),
            },
            headers=_HEADERS,
            name="/v1/memory/semantic/facts",
        )

    @task(10)
    def query_facts(self) -> None:
        """Query the semantic knowledge graph."""
        self.client.post(
            "/v1/memory/semantic/query",
            json={
                "agent_id": self.agent_id,
                "query": random.choice(_QUERIES),
                "k": 5,
            },
            headers=_HEADERS,
            name="/v1/memory/semantic/query",
        )

    @task(5)
    def match_procedure(self) -> None:
        """Find a matching procedure."""
        tasks = ["deploy the application", "send an email", "parse a CSV file", "run tests"]
        self.client.post(
            "/v1/memory/procedural/match",
            json={
                "agent_id": self.agent_id,
                "task_description": random.choice(tasks),
                "k": 3,
            },
            headers=_HEADERS,
            name="/v1/memory/procedural/match",
        )

    @task(5)
    def health_check(self) -> None:
        """Health check — should always be fast."""
        self.client.get("/health", name="/health")
