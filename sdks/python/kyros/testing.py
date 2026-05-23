"""Test data generators and testing utilities for Kyros.

This module provides tools for generating test data, mocking responses,
and testing memory operations.

Example:
    ```python
    from kyros.testing import TestDataGenerator, MockKyrosClient

    # Generate test memories
    generator = TestDataGenerator()
    memories = generator.generate_memories(count=100, agent_id="test-user")

    # Use mock client for testing
    mock_client = MockKyrosClient()
    mock_client.add_mock_memory("user123", "User prefers dark mode")
    ```
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta
from typing import Any, cast

from .client import KyrosClient


class TestDataGenerator:
    """Generate realistic test data for Kyros.

    Useful for testing, development, and demonstrations.
    """

    # Sample data for generating realistic memories
    SAMPLE_FACTS = [
        "User prefers dark mode",
        "User is a Premium member",
        "User's timezone is UTC-8",
        "User speaks English and Spanish",
        "User prefers email notifications",
        "User's favorite color is blue",
        "User works in software engineering",
        "User is interested in AI and machine learning",
        "User has a cat named Whiskers",
        "User exercises 3 times per week",
        "User is vegetarian",
        "User's birthday is in March",
        "User prefers morning meetings",
        "User uses macOS",
        "User's favorite programming language is Python",
    ]

    SAMPLE_EVENTS = [
        "User completed onboarding",
        "User upgraded to Premium plan",
        "User changed password",
        "User updated profile picture",
        "User added payment method",
        "User invited 3 team members",
        "User created first project",
        "User completed tutorial",
        "User reached 100 tasks milestone",
        "User enabled two-factor authentication",
        "User connected GitHub account",
        "User exported data",
        "User attended webinar",
        "User submitted feedback",
        "User reported a bug",
    ]

    SAMPLE_PROCEDURES = [
        ("Reset Password", [
            "Click 'Forgot Password' link",
            "Enter email address",
            "Check email for reset link",
            "Click reset link",
            "Enter new password",
            "Confirm password change",
        ]),
        ("Create Project", [
            "Click 'New Project' button",
            "Enter project name",
            "Select project template",
            "Add team members",
            "Set project permissions",
            "Click 'Create' to finish",
        ]),
        ("Export Data", [
            "Go to Settings",
            "Click 'Data & Privacy'",
            "Select 'Export Data'",
            "Choose export format",
            "Click 'Start Export'",
            "Download when ready",
        ]),
    ]

    def __init__(self, seed: int | None = None) -> None:
        """Initialize test data generator.

        Args:
            seed: Random seed for reproducibility (optional)
        """
        if seed is not None:
            random.seed(seed)

    def generate_memories(
        self,
        count: int = 10,
        agent_id: str | None = None,
        memory_types: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Generate random memories.

        Args:
            count: Number of memories to generate
            agent_id: Agent ID (generates random if None)
            memory_types: Types to generate (default: all types)

        Returns:
            List of memory objects
        """
        if agent_id is None:
            agent_id = f"test-user-{uuid.uuid4().hex[:8]}"

        if memory_types is None:
            memory_types = ["semantic", "episodic", "procedural"]

        memories = []

        for _i in range(count):
            memory_type = random.choice(memory_types)

            if memory_type == "semantic":
                memory = self.generate_semantic_memory(agent_id)
            elif memory_type == "episodic":
                memory = self.generate_episodic_memory(agent_id)
            else:
                memory = self.generate_procedural_memory(agent_id)

            memories.append(memory)

        return memories

    def generate_semantic_memory(self, agent_id: str) -> dict[str, Any]:
        """Generate a semantic memory (fact).

        Args:
            agent_id: Agent ID

        Returns:
            Semantic memory object
        """
        content = random.choice(self.SAMPLE_FACTS)
        importance = random.uniform(0.3, 1.0)

        return {
            "type": "semantic",
            "agent_id": agent_id,
            "content": content,
            "importance": round(importance, 2),
            "metadata": {
                "source": "test_generator",
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def generate_episodic_memory(self, agent_id: str) -> dict[str, Any]:
        """Generate an episodic memory (event).

        Args:
            agent_id: Agent ID

        Returns:
            Episodic memory object
        """
        event = random.choice(self.SAMPLE_EVENTS)
        importance = random.uniform(0.4, 0.9)

        # Random time in the past 30 days
        days_ago = random.randint(0, 30)
        occurred_at = datetime.utcnow() - timedelta(days=days_ago)

        return {
            "type": "episodic",
            "agent_id": agent_id,
            "event_description": event,
            "importance": round(importance, 2),
            "occurred_at": occurred_at.isoformat(),
            "metadata": {
                "source": "test_generator",
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def generate_procedural_memory(self, agent_id: str) -> dict[str, Any]:
        """Generate a procedural memory (process).

        Args:
            agent_id: Agent ID

        Returns:
            Procedural memory object
        """
        name, steps = random.choice(self.SAMPLE_PROCEDURES)

        return {
            "type": "procedural",
            "agent_id": agent_id,
            "name": name,
            "steps": steps,
            "metadata": {
                "source": "test_generator",
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def generate_conversation(
        self,
        turns: int = 5,
        include_memories: bool = True,
    ) -> list[dict[str, str]]:
        """Generate a sample conversation.

        Args:
            turns: Number of conversation turns
            include_memories: Include memory-related content

        Returns:
            List of message objects
        """
        conversation = []

        topics = [
            ("preferences", [
                "I prefer dark mode",
                "I like to receive email notifications",
                "I work best in the morning",
            ]),
            ("profile", [
                "I'm a software engineer",
                "I speak English and Spanish",
                "I'm interested in AI",
            ]),
            ("activities", [
                "I just completed the tutorial",
                "I upgraded to Premium",
                "I invited my team",
            ]),
        ]

        for i in range(turns):
            if i % 2 == 0:
                # User message
                if include_memories and random.random() > 0.5:
                    topic, messages = random.choice(topics)
                    content = random.choice(messages)
                else:
                    content = f"This is user message {i+1}"

                conversation.append({
                    "role": "user",
                    "content": content,
                })
            else:
                # Assistant message
                conversation.append({
                    "role": "assistant",
                    "content": "I understand. Let me help you with that.",
                })

        return conversation

    def generate_agent_profile(self) -> dict[str, Any]:
        """Generate a complete agent profile with memories.

        Returns:
            Agent profile with memories
        """
        agent_id = f"test-user-{uuid.uuid4().hex[:8]}"

        return {
            "agent_id": agent_id,
            "display_name": f"Test User {agent_id[-4:]}",
            "created_at": datetime.utcnow().isoformat(),
            "memories": self.generate_memories(count=20, agent_id=agent_id),
            "metadata": {
                "source": "test_generator",
                "generated_at": datetime.utcnow().isoformat(),
            },
        }

    def bulk_generate(
        self,
        num_agents: int = 10,
        memories_per_agent: int = 20,
    ) -> list[dict[str, Any]]:
        """Generate multiple agent profiles with memories.

        Args:
            num_agents: Number of agents to generate
            memories_per_agent: Memories per agent

        Returns:
            List of agent profiles
        """
        print(f"\n🔧 Generating {num_agents} agents with {memories_per_agent} memories each...")

        profiles = []
        for i in range(num_agents):
            agent_id = f"test-user-{i:04d}"
            profile = {
                "agent_id": agent_id,
                "display_name": f"Test User {i+1}",
                "memories": self.generate_memories(
                    count=memories_per_agent,
                    agent_id=agent_id,
                ),
            }
            profiles.append(profile)

        print(f"✅ Generated {num_agents} agent profiles")
        return profiles


class MockKyrosClient:
    """Mock Kyros client for testing.

    Simulates Kyros API without making real requests.
    """

    def __init__(self) -> None:
        """Initialize mock client."""
        self.memories: dict[str, list[dict[str, Any]]] = {}
        self.call_count = 0

    def add_mock_memory(
        self,
        agent_id: str,
        content: str,
        memory_type: str = "semantic",
        importance: float = 0.7,
    ) -> None:
        """Add a mock memory.

        Args:
            agent_id: Agent ID
            content: Memory content
            memory_type: Memory type
            importance: Importance score
        """
        if agent_id not in self.memories:
            self.memories[agent_id] = []

        self.memories[agent_id].append({
            "id": str(uuid.uuid4()),
            "type": memory_type,
            "content": content,
            "importance": importance,
            "agent_id": agent_id,
        })

    def recall(self, agent_id: str, query: str, k: int = 5) -> dict[str, Any]:
        """Mock recall operation.

        Args:
            agent_id: Agent ID
            query: Search query
            k: Number of results

        Returns:
            Mock recall response
        """
        self.call_count += 1

        memories = self.memories.get(agent_id, [])

        # Simple mock: return first k memories
        results = memories[:k]

        return {
            "results": results,
            "count": len(results),
        }

    def store(self, agent_id: str, content: str, **kwargs: Any) -> dict[str, Any]:
        """Mock store operation.

        Args:
            agent_id: Agent ID
            content: Memory content
            **kwargs: Additional parameters

        Returns:
            Mock store response
        """
        self.call_count += 1

        memory_id = str(uuid.uuid4())
        self.add_mock_memory(agent_id, content, **kwargs)

        return {
            "id": memory_id,
            "success": True,
        }

    def get_call_count(self) -> int:
        """Get number of API calls made.

        Returns:
            Call count
        """
        return self.call_count

    def reset(self) -> None:
        """Reset mock client state."""
        self.memories = {}
        self.call_count = 0


class MemoryValidator:
    """Validate memory data and operations.

    Ensures memories meet quality standards.
    """

    @staticmethod
    def validate_memory(memory: dict[str, Any]) -> tuple[bool, list[str]]:
        """Validate a memory object.

        Args:
            memory: Memory object to validate

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []

        # Check required fields
        required_fields = ["agent_id", "type"]
        for field in required_fields:
            if field not in memory:
                errors.append(f"Missing required field: {field}")

        # Validate memory type
        valid_types = ["semantic", "episodic", "procedural"]
        if memory.get("type") not in valid_types:
            errors.append(f"Invalid memory type: {memory.get('type')}")

        # Validate importance
        importance = memory.get("importance")
        if importance is not None:
            if not isinstance(importance, (int, float)):
                errors.append("Importance must be a number")
            elif not 0 <= importance <= 1:
                errors.append("Importance must be between 0 and 1")

        # Type-specific validation
        mem_type = memory.get("type")
        if mem_type == "semantic":
            if "content" not in memory:
                errors.append("Semantic memory must have 'content' field")
        elif mem_type == "episodic":
            if "event_description" not in memory:
                errors.append("Episodic memory must have 'event_description' field")
        elif mem_type == "procedural" and ("name" not in memory or "steps" not in memory):
            errors.append("Procedural memory must have 'name' and 'steps' fields")

        return len(errors) == 0, errors

    @staticmethod
    def validate_batch(memories: list[dict[str, Any]]) -> dict[str, Any]:
        """Validate a batch of memories.

        Args:
            memories: List of memory objects

        Returns:
            Validation report
        """
        report: dict[str, Any] = {
            "total": len(memories),
            "valid": 0,
            "invalid": 0,
            "errors": [],
        }

        for i, memory in enumerate(memories):
            is_valid, errors = MemoryValidator.validate_memory(memory)

            if is_valid:
                report["valid"] += 1
            else:
                report["invalid"] += 1
                report["errors"].append({
                    "index": i,
                    "memory_id": memory.get("id", "unknown"),
                    "errors": errors,
                })

        return report


def load_test_data(client: KyrosClient, num_agents: int = 5, memories_per_agent: int = 10) -> None:
    """Load test data into Kyros.

    Args:
        client: Kyros client
        num_agents: Number of test agents
        memories_per_agent: Memories per agent
    """
    print("\n🔧 Loading test data into Kyros...")
    print(f"   Agents: {num_agents}")
    print(f"   Memories per agent: {memories_per_agent}")

    generator = TestDataGenerator()
    profiles = generator.bulk_generate(num_agents, memories_per_agent)

    total_stored = 0

    for profile in profiles:
        agent_id = str(profile["agent_id"])
        memories = cast(list[dict[str, Any]], profile["memories"])

        for memory in memories:
            try:
                # Store memory based on type
                if memory["type"] == "semantic":
                    client.post("/v1/memory/smart/store", json={
                        "agent_id": agent_id,
                        "content": memory["content"],
                    })
                elif memory["type"] == "episodic":
                    client.post("/v1/memory/smart/store", json={
                        "agent_id": agent_id,
                        "content": memory["event_description"],
                        "timestamp": memory["occurred_at"],
                    })
                elif memory["type"] == "procedural":
                    client.post("/v1/memory/smart/store", json={
                        "agent_id": agent_id,
                        "content": f"{memory['name']}: {', '.join(memory['steps'])}",
                    })

                total_stored += 1
            except Exception as e:
                print(f"   ⚠️  Failed to store memory: {e}")

    print(f"\n✅ Loaded {total_stored} memories for {num_agents} agents")


def run_integration_test(client: KyrosClient, agent_id: str = "test-integration") -> dict[str, Any]:
    """Run integration test of Kyros operations.

    Args:
        client: Kyros client
        agent_id: Agent ID for testing

    Returns:
        Test results
    """
    print(f"\n🧪 Running integration test for agent: {agent_id}\n")

    results: dict[str, Any] = {
        "agent_id": agent_id,
        "tests": [],
        "passed": 0,
        "failed": 0,
    }

    # Test 1: Store semantic memory
    try:
        response = client.post("/v1/memory/smart/store", json={
            "agent_id": agent_id,
            "content": "Integration test memory",
        })

        if response.status_code in (200, 201):
            results["tests"].append({"name": "Store semantic memory", "status": "PASS"})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Store semantic memory", "status": "FAIL"})
            results["failed"] += 1
    except Exception as e:
        results["tests"].append(
            {"name": "Store semantic memory", "status": "ERROR", "error": str(e)}
        )
        results["failed"] += 1

    # Test 2: Recall memories
    try:
        response = client.post("/v1/memory/episodic/recall", json={
            "agent_id": agent_id,
            "query": "test",
            "k": 5,
        })

        if response.status_code == 200:
            results["tests"].append({"name": "Recall memories", "status": "PASS"})
            results["passed"] += 1
        else:
            results["tests"].append({"name": "Recall memories", "status": "FAIL"})
            results["failed"] += 1
    except Exception as e:
        results["tests"].append({"name": "Recall memories", "status": "ERROR", "error": str(e)})
        results["failed"] += 1

    # Print results
    print("=" * 60)
    print("INTEGRATION TEST RESULTS")
    print("=" * 60)

    for test in results["tests"]:
        status_icon = "✅" if test["status"] == "PASS" else "❌"
        print(f"{status_icon} {test['name']}: {test['status']}")
        if "error" in test:
            print(f"   Error: {test['error']}")

    print(f"\nPassed: {results['passed']}/{len(results['tests'])}")
    print(f"Failed: {results['failed']}/{len(results['tests'])}")
    print("=" * 60)

    return results
