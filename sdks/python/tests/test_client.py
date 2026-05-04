"""Tests for Kyros client."""

import pytest

from kyros import AuthenticationError, KyrosClient


def test_client_initialization_with_api_key():
    """Test client initialization with API key."""
    client = KyrosClient(api_key="test-key")
    assert client.api_key == "test-key"
    assert client.base_url == "https://api.kyros.ai"
    assert client.timeout == 30.0
    client.close()


def test_client_initialization_without_api_key():
    """Test client initialization without API key raises error."""
    with pytest.raises(AuthenticationError):
        KyrosClient()


def test_client_initialization_with_custom_base_url():
    """Test client initialization with custom base URL."""
    client = KyrosClient(
        api_key="test-key",
        base_url="https://custom.kyros.ai"
    )
    assert client.base_url == "https://custom.kyros.ai"
    client.close()


def test_client_initialization_with_custom_timeout():
    """Test client initialization with custom timeout."""
    client = KyrosClient(api_key="test-key", timeout=60.0)
    assert client.timeout == 60.0
    client.close()


def test_client_context_manager():
    """Test client as context manager."""
    with KyrosClient(api_key="test-key") as client:
        assert client.api_key == "test-key"
    # Client should be closed after context


@pytest.mark.integration
def test_remember(client: KyrosClient, agent_id: str):
    """Test storing episodic memory."""
    response = client.remember(
        agent_id=agent_id,
        content="Test memory content",
        importance=0.8
    )
    assert response.memory_id
    assert response.agent_id == agent_id
    assert response.memory_type == "episodic"


@pytest.mark.integration
def test_recall(client: KyrosClient, agent_id: str):
    """Test recalling memories."""
    # First store a memory
    client.remember(
        agent_id=agent_id,
        content="User prefers dark mode"
    )

    # Then recall it
    results = client.recall(
        agent_id=agent_id,
        query="user preferences",
        k=5
    )
    assert results.agent_id == agent_id
    assert isinstance(results.results, list)


@pytest.mark.integration
def test_store_fact(client: KyrosClient, agent_id: str):
    """Test storing semantic fact."""
    fact = client.store_fact(
        agent_id=agent_id,
        subject="user",
        predicate="prefers",
        value="dark mode",
        confidence=0.9
    )
    assert fact.fact_id
    assert fact.subject == "user"
    assert fact.predicate == "prefers"
    assert fact.object == "dark mode"


@pytest.mark.integration
def test_store_procedure(client: KyrosClient, agent_id: str):
    """Test storing procedure."""
    procedure = client.store_procedure(
        agent_id=agent_id,
        name="Send Email",
        description="Send an email to a recipient",
        task_type="communication",
        steps=[
            {"action": "compose", "params": {"to": "user@example.com"}},
            {"action": "send"}
        ]
    )
    assert procedure.procedure_id
    assert procedure.name == "Send Email"


@pytest.mark.integration
def test_search(client: KyrosClient, agent_id: str):
    """Test unified search."""
    results = client.search(
        agent_id=agent_id,
        query="test query",
        k=10
    )
    assert results.agent_id == agent_id
    assert isinstance(results.results, list)
