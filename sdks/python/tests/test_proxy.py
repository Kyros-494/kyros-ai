"""Tests for KyrosProxy."""

from typing import Any
from unittest.mock import Mock, patch

import pytest

from kyros import KyrosProxy
from kyros.exceptions import KyrosError


class TestKyrosProxyInit:
    """Test KyrosProxy initialization."""

    def test_init_with_kyros_key_only(self) -> None:
        """Test initialization with only Kyros API key."""
        proxy = KyrosProxy(kyros_api_key="mk_test_123")
        assert proxy.kyros is not None
        assert proxy.memory_k == 5
        assert proxy.auto_store is True
        assert proxy.debug is False

    def test_init_with_custom_settings(self) -> None:
        """Test initialization with custom settings."""
        proxy = KyrosProxy(
            kyros_api_key="mk_test_123",
            memory_k=10,
            auto_store=False,
            debug=True,
            memory_importance=0.8,
        )
        assert proxy.memory_k == 10
        assert proxy.auto_store is False
        assert proxy.debug is True
        assert proxy.memory_importance == 0.8

    @patch("kyros.proxy.openai")
    def test_init_with_openai_key(self, mock_openai: Mock) -> None:
        """Test initialization with OpenAI API key."""
        mock_openai.OpenAI.return_value = Mock()
        proxy = KyrosProxy(
            kyros_api_key="mk_test_123", openai_api_key="sk-test"
        )
        assert proxy._openai_client is not None
        mock_openai.OpenAI.assert_called_once_with(api_key="sk-test")

    def test_init_without_openai_package(self) -> None:
        """Test initialization fails gracefully without openai package."""
        with patch.dict("sys.modules", {"openai": None}), pytest.raises(
            ImportError, match="openai package is required"
        ):
            KyrosProxy(kyros_api_key="mk_test_123", openai_api_key="sk-test")


class TestKyrosProxyChat:
    """Test KyrosProxy chat method."""

    @pytest.fixture
    def mock_proxy(self) -> Any:
        """Create a mock proxy with mocked dependencies."""
        with patch("kyros.proxy.openai") as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            proxy = KyrosProxy(
                kyros_api_key="mk_test_123",
                openai_api_key="sk-test",
                debug=False,
            )

            # Mock Kyros client methods
            proxy.kyros.recall = Mock()
            proxy.kyros.post = Mock()

            yield proxy, mock_client

    def test_chat_with_no_memories(self, mock_proxy: Any) -> None:
        """Test chat when no memories are found."""
        proxy, mock_client = mock_proxy

        # Mock no memories found
        mock_recall_response = Mock()
        mock_recall_response.results = []
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat
        response = proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify
        assert response == mock_response
        proxy.kyros.recall.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()

    def test_chat_with_memories(self, mock_proxy: Any) -> None:
        """Test chat with memories recalled."""
        proxy, mock_client = mock_proxy

        # Mock memories found
        mock_memory = Mock()
        mock_memory.content = "User prefers dark mode"
        mock_memory.relevance_score = 0.95

        mock_recall_response = Mock()
        mock_recall_response.results = [mock_memory]
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [
            Mock(message=Mock(content="You prefer dark mode"))
        ]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat
        response = proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "What's my preference?"}],
        )

        # Verify
        assert response == mock_response
        proxy.kyros.recall.assert_called_once_with(
            agent_id="user123", query="What's my preference?", k=5
        )

        # Verify memory context was injected
        call_args = mock_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]
        assert any("User prefers dark mode" in str(m) for m in messages)

    def test_chat_stores_conversation(self, mock_proxy: Any) -> None:
        """Test that conversation is stored after chat."""
        proxy, mock_client = mock_proxy

        # Mock no memories
        mock_recall_response = Mock()
        mock_recall_response.results = []
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello there!"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat
        proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify storage was called twice (user + assistant)
        assert proxy.kyros.post.call_count == 2

        # Verify user message stored
        first_call = proxy.kyros.post.call_args_list[0]
        assert "User: Hi" in str(first_call)

        # Verify assistant message stored
        second_call = proxy.kyros.post.call_args_list[1]
        assert "Assistant: Hello there!" in str(second_call)

    def test_chat_with_auto_store_disabled(self, mock_proxy: Any) -> None:
        """Test chat with auto_store disabled."""
        proxy, mock_client = mock_proxy
        proxy.auto_store = False

        # Mock no memories
        mock_recall_response = Mock()
        mock_recall_response.results = []
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat
        proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify storage was NOT called
        proxy.kyros.post.assert_not_called()

    def test_chat_handles_recall_failure(self, mock_proxy: Any) -> None:
        """Test chat continues even if memory recall fails."""
        proxy, mock_client = mock_proxy

        # Mock recall failure
        proxy.kyros.recall.side_effect = KyrosError("Recall failed")

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat - should not raise
        response = proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify chat still worked
        assert response == mock_response

    def test_chat_handles_storage_failure(self, mock_proxy: Any) -> None:
        """Test chat continues even if memory storage fails."""
        proxy, mock_client = mock_proxy

        # Mock no memories
        mock_recall_response = Mock()
        mock_recall_response.results = []
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock storage failure
        proxy.kyros.post.side_effect = KyrosError("Storage failed")

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello!"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat - should not raise
        response = proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify chat still worked
        assert response == mock_response

    def test_chat_with_unsupported_model(self, mock_proxy: Any) -> None:
        """Test chat with unsupported model raises error."""
        proxy, _ = mock_proxy

        with pytest.raises(ValueError, match="not supported"):
            proxy.chat(
                model="unsupported-model",
                agent_id="user123",
                messages=[{"role": "user", "content": "Hi"}],
            )

    def test_chat_without_openai_client(self) -> None:
        """Test chat with gpt model but no OpenAI client."""
        proxy = KyrosProxy(kyros_api_key="mk_test_123")

        with pytest.raises(ValueError, match="OpenAI client not initialized"):
            proxy.chat(
                model="gpt-4",
                agent_id="user123",
                messages=[{"role": "user", "content": "Hi"}],
            )


class TestKyrosProxyDebugMode:
    """Test KyrosProxy debug mode."""

    @pytest.fixture
    def debug_proxy(self) -> Any:
        """Create a proxy with debug mode enabled."""
        with patch("kyros.proxy.openai") as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            proxy = KyrosProxy(
                kyros_api_key="mk_test_123",
                openai_api_key="sk-test",
                debug=True,
            )

            proxy.kyros.recall = Mock()
            proxy.kyros.post = Mock()

            yield proxy, mock_client

    def test_debug_mode_prints_messages(self, debug_proxy: Any, capsys: Any) -> None:
        """Test debug mode prints debug messages."""
        proxy, mock_client = debug_proxy

        # Mock memories
        mock_memory = Mock()
        mock_memory.content = "User prefers dark mode"
        mock_memory.relevance_score = 0.95

        mock_recall_response = Mock()
        mock_recall_response.results = [mock_memory]
        proxy.kyros.recall.return_value = mock_recall_response

        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Response"))]
        mock_client.chat.completions.create.return_value = mock_response

        # Call chat
        proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hi"}],
        )

        # Verify debug output
        captured = capsys.readouterr()
        assert "[Kyros Debug]" in captured.out
        assert "Starting chat for agent: user123" in captured.out
        assert "Model: gpt-4" in captured.out
        assert "Found 1 memories" in captured.out


class TestKyrosProxyContextManager:
    """Test KyrosProxy context manager."""

    def test_context_manager(self) -> None:
        """Test proxy works as context manager."""
        with patch("kyros.proxy.openai"), KyrosProxy(
            kyros_api_key="mk_test_123", openai_api_key="sk-test"
        ) as proxy:
            assert proxy is not None
            assert proxy.kyros is not None


class TestKyrosProxyMultiLLM:
    """Test KyrosProxy with multiple LLM providers."""

    def test_anthropic_support(self) -> None:
        """Test Anthropic model support."""
        with patch("kyros.proxy.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            proxy = KyrosProxy(
                kyros_api_key="mk_test_123", anthropic_api_key="sk-ant-test"
            )

            # Mock no memories
            mock_recall_response = Mock()
            mock_recall_response.results = []
            proxy.kyros.recall = Mock(return_value=mock_recall_response)
            proxy.kyros.post = Mock()

            # Mock Anthropic response
            mock_response = Mock()
            mock_response.content = [Mock(text="Hello from Claude")]
            mock_client.messages.create.return_value = mock_response

            # Call chat
            response = proxy.chat(
                model="claude-3-opus",
                agent_id="user123",
                messages=[{"role": "user", "content": "Hi"}],
            )

            # Verify
            assert response == mock_response
            mock_client.messages.create.assert_called_once()

    def test_google_support(self) -> None:
        """Test Google Gemini model support."""
        with patch("kyros.proxy.genai") as mock_genai:
            mock_model = Mock()
            mock_genai.GenerativeModel.return_value = mock_model

            proxy = KyrosProxy(
                kyros_api_key="mk_test_123", google_api_key="google-test"
            )

            # Mock no memories
            mock_recall_response = Mock()
            mock_recall_response.results = []
            proxy.kyros.recall = Mock(return_value=mock_recall_response)
            proxy.kyros.post = Mock()

            # Mock Google response
            mock_response = Mock()
            mock_response.text = "Hello from Gemini"
            mock_model.generate_content.return_value = mock_response

            # Call chat
            response = proxy.chat(
                model="gemini-pro",
                agent_id="user123",
                messages=[{"role": "user", "content": "Hi"}],
            )

            # Verify
            assert response == mock_response
            mock_model.generate_content.assert_called_once()


class TestKyrosProxyMemoryInjection:
    """Test memory context injection."""

    def test_memory_injected_after_system_messages(self) -> None:
        """Test memory context is injected after system messages."""
        with patch("kyros.proxy.openai") as mock_openai:
            mock_client = Mock()
            mock_openai.OpenAI.return_value = mock_client

            proxy = KyrosProxy(
                kyros_api_key="mk_test_123", openai_api_key="sk-test"
            )

            # Mock memory
            mock_memory = Mock()
            mock_memory.content = "User prefers dark mode"
            mock_memory.relevance_score = 0.95

            mock_recall_response = Mock()
            mock_recall_response.results = [mock_memory]
            proxy.kyros.recall = Mock(return_value=mock_recall_response)
            proxy.kyros.post = Mock()

            # Mock OpenAI response
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="Response"))]
            mock_client.chat.completions.create.return_value = mock_response

            # Call chat with system message
            proxy.chat(
                model="gpt-4",
                agent_id="user123",
                messages=[
                    {"role": "system", "content": "You are helpful"},
                    {"role": "user", "content": "Hi"},
                ],
            )

            # Verify memory was injected after system message
            call_args = mock_client.chat.completions.create.call_args
            messages = call_args.kwargs["messages"]

            # Should be: system, memory, user
            assert len(messages) == 3
            assert messages[0]["role"] == "system"
            assert messages[0]["content"] == "You are helpful"
            assert messages[1]["role"] == "system"
            assert "User prefers dark mode" in messages[1]["content"]
            assert messages[2]["role"] == "user"
