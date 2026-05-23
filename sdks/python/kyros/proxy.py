"""LLM Proxy with automatic memory management.

This module provides a unified interface for calling LLMs (OpenAI, Anthropic, Google)
with automatic memory recall and storage via Kyros.

Example:
    ```python
    from kyros import KyrosProxy

    proxy = KyrosProxy(
        kyros_api_key="mk_live_...",
        openai_api_key="sk-...",
        debug=True
    )

    # One line replaces 50+ lines of manual memory management!
    response = proxy.chat(
        model="gpt-4",
        agent_id="user123",
        messages=[{"role": "user", "content": "What's my preference?"}]
    )

    print(response.choices[0].message.content)
    # → "You prefer dark mode" (from memory!)
    ```
"""

from __future__ import annotations

from typing import Any

from .client import KyrosClient
from .exceptions import KyrosError

try:
    import openai  # type: ignore[import-not-found]
except ImportError:
    openai = None

try:
    import anthropic  # type: ignore[import-not-found]
except ImportError:
    anthropic = None

try:
    import google.generativeai as genai  # type: ignore[import-not-found]
except ImportError:
    genai = None


class KyrosProxy:
    """LLM Proxy with automatic memory management.

    This proxy sits between your application and LLMs (OpenAI, Anthropic, Google),
    automatically handling memory recall and storage.

    Features:
        - Automatic memory recall before LLM calls
        - Automatic memory storage after LLM responses
        - Support for multiple LLM providers
        - Debug mode for troubleshooting
        - Configurable memory settings

    Args:
        kyros_api_key: Kyros API key for memory operations
        openai_api_key: OpenAI API key (optional)
        anthropic_api_key: Anthropic API key (optional)
        google_api_key: Google API key (optional)
        memory_k: Number of memories to recall per request (default: 5)
        auto_store: Automatically store conversations (default: True)
        debug: Enable debug logging (default: False)
        memory_importance: Default importance for stored memories (default: 0.5)

    Example:
        ```python
        proxy = KyrosProxy(
            kyros_api_key="mk_live_...",
            openai_api_key="sk-...",
            memory_k=10,
            debug=True
        )

        response = proxy.chat(
            model="gpt-4",
            agent_id="user123",
            messages=[{"role": "user", "content": "Hello"}]
        )
        ```
    """

    def __init__(
        self,
        kyros_api_key: str,
        openai_api_key: str | None = None,
        anthropic_api_key: str | None = None,
        google_api_key: str | None = None,
        memory_k: int = 5,
        auto_store: bool = True,
        debug: bool = False,
        memory_importance: float = 0.5,
    ) -> None:
        """Initialize KyrosProxy with API keys and settings."""
        # Initialize Kyros client
        self.kyros = KyrosClient(api_key=kyros_api_key)
        self.memory_k = memory_k
        self.auto_store = auto_store
        self.debug = debug
        self.memory_importance = memory_importance

        # Initialize LLM clients
        self._openai_client = None
        self._anthropic_client = None
        self._google_model = None

        if openai_api_key:
            if openai is None:
                raise ImportError(
                    "openai package is required for OpenAI support. "
                    "Install it with: pip install openai"
                )

            self._openai_client = openai.OpenAI(api_key=openai_api_key)
            if self.debug:
                print("[Kyros Debug] OpenAI client initialized")

        if anthropic_api_key:
            if anthropic is None:
                raise ImportError(
                    "anthropic package is required for Anthropic support. "
                    "Install it with: pip install anthropic"
                )

            self._anthropic_client = anthropic.Anthropic(api_key=anthropic_api_key)
            if self.debug:
                print("[Kyros Debug] Anthropic client initialized")

        if google_api_key:
            if genai is None:
                raise ImportError(
                    "google-generativeai package is required for Google support. "
                    "Install it with: pip install google-generativeai"
                )

            genai.configure(api_key=google_api_key)
            self._google_configured = True
            if self.debug:
                print("[Kyros Debug] Google AI configured")

    def chat(
        self,
        model: str,
        agent_id: str,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> Any:
        """Chat with automatic memory management.

        This method:
        1. Recalls relevant memories for the agent
        2. Adds memories to the conversation context
        3. Calls the appropriate LLM
        4. Stores the conversation in Kyros
        5. Returns the LLM response

        Args:
            model: Model name (e.g., "gpt-4", "claude-3-opus", "gemini-pro")
            agent_id: Unique identifier for the agent/user
            messages: List of message dicts with "role" and "content"
            **kwargs: Additional arguments passed to the LLM

        Returns:
            LLM response object (format depends on provider)

        Raises:
            ValueError: If model is not supported or client not initialized
            KyrosError: If memory operations fail

        Example:
            ```python
            response = proxy.chat(
                model="gpt-4",
                agent_id="user123",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant"},
                    {"role": "user", "content": "What's my preference?"}
                ]
            )
            ```
        """
        if self.debug:
            print(f"[Kyros Debug] Starting chat for agent: {agent_id}")
            print(f"[Kyros Debug] Model: {model}")

        if not model.startswith(("gpt", "claude", "gemini")):
            raise ValueError(
                f"Model '{model}' not supported. "
                f"Supported prefixes: gpt, claude, gemini"
            )

        # Extract user query from last message
        user_query = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_query = msg.get("content", "")
                break

        if self.debug:
            print(f"[Kyros Debug] User query: {user_query[:100]}...")

        # 1. Recall relevant memories
        memories_context = self._recall_memories(agent_id, user_query)

        # 2. Add memories to context
        if memories_context:
            messages = self._inject_memory_context(messages, memories_context)

        # 3. Call appropriate LLM
        if model.startswith("gpt"):
            response = self._call_openai(model, messages, **kwargs)
            assistant_message = response.choices[0].message.content
        elif model.startswith("claude"):
            response = self._call_anthropic(model, messages, **kwargs)
            assistant_message = response.content[0].text
        elif model.startswith("gemini"):
            response = self._call_google(model, messages, **kwargs)
            assistant_message = response.text

        if self.debug:
            print(f"[Kyros Debug] LLM response: {assistant_message[:100]}...")

        # 4. Store conversation
        if self.auto_store:
            self._store_conversation(agent_id, user_query, assistant_message)

        return response

    def _recall_memories(self, agent_id: str, query: str) -> str:
        """Recall relevant memories for the agent.

        Args:
            agent_id: Agent identifier
            query: Search query

        Returns:
            Formatted memory context string
        """
        if not query.strip():
            return ""

        try:
            if self.debug:
                print(f"[Kyros Debug] Recalling memories (k={self.memory_k})...")

            response = self.kyros.recall(
                agent_id=agent_id, query=query, k=self.memory_k
            )

            if not response.results:
                if self.debug:
                    print("[Kyros Debug] No memories found")
                return ""

            if self.debug:
                print(f"[Kyros Debug] Found {len(response.results)} memories:")
                for i, mem in enumerate(response.results, 1):
                    print(
                        f"[Kyros Debug]   {i}. {mem.content[:60]}... "
                        f"(score: {mem.relevance_score:.2f})"
                    )

            # Format memories as context
            context_lines = []
            for mem in response.results:
                context_lines.append(f"- {mem.content}")

            return "\n".join(context_lines)

        except KyrosError as e:
            if self.debug:
                print(f"[Kyros Debug] Memory recall failed: {e}")
            # Don't fail the entire request if memory recall fails
            return ""

    def _inject_memory_context(
        self, messages: list[dict[str, str]], context: str
    ) -> list[dict[str, str]]:
        """Inject memory context into messages.

        Args:
            messages: Original messages
            context: Memory context to inject

        Returns:
            Messages with memory context injected
        """
        memory_message = {
            "role": "system",
            "content": f"Relevant memories about this user:\n{context}",
        }

        # Insert after any existing system messages
        insert_index = 0
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                insert_index = i + 1

        messages_copy = messages.copy()
        messages_copy.insert(insert_index, memory_message)

        if self.debug:
            print(f"[Kyros Debug] Injected memory context at position {insert_index}")

        return messages_copy

    def _store_conversation(
        self, agent_id: str, user_message: str, assistant_message: str
    ) -> None:
        """Store conversation in Kyros.

        Args:
            agent_id: Agent identifier
            user_message: User's message
            assistant_message: Assistant's response
        """
        try:
            if self.debug:
                print("[Kyros Debug] Storing conversation...")

            # Store user message
            if user_message.strip():
                self.kyros.post(
                    "/v1/memory/smart/store",
                    json={
                        "agent_id": agent_id,
                        "content": f"User: {user_message}",
                    },
                )

            # Store assistant message
            if assistant_message.strip():
                self.kyros.post(
                    "/v1/memory/smart/store",
                    json={
                        "agent_id": agent_id,
                        "content": f"Assistant: {assistant_message}",
                    },
                )

            if self.debug:
                print("[Kyros Debug] Conversation stored successfully")

        except KyrosError as e:
            if self.debug:
                print(f"[Kyros Debug] Memory storage failed: {e}")
            # Don't fail the entire request if storage fails

    def _call_openai(
        self, model: str, messages: list[dict[str, str]], **kwargs: Any
    ) -> Any:
        """Call OpenAI API.

        Args:
            model: Model name
            messages: Messages
            **kwargs: Additional arguments

        Returns:
            OpenAI response

        Raises:
            ValueError: If OpenAI client not initialized
        """
        if not self._openai_client:
            raise ValueError(
                "OpenAI client not initialized. "
                "Pass openai_api_key to KyrosProxy constructor."
            )

        if self.debug:
            print(f"[Kyros Debug] Calling OpenAI with model: {model}")

        return self._openai_client.chat.completions.create(
            model=model, messages=messages, **kwargs
        )

    def _call_anthropic(
        self, model: str, messages: list[dict[str, str]], **kwargs: Any
    ) -> Any:
        """Call Anthropic API.

        Args:
            model: Model name
            messages: Messages
            **kwargs: Additional arguments

        Returns:
            Anthropic response

        Raises:
            ValueError: If Anthropic client not initialized
        """
        if not self._anthropic_client:
            raise ValueError(
                "Anthropic client not initialized. "
                "Pass anthropic_api_key to KyrosProxy constructor."
            )

        if self.debug:
            print(f"[Kyros Debug] Calling Anthropic with model: {model}")

        # Convert messages format for Anthropic
        system_messages = [m["content"] for m in messages if m["role"] == "system"]
        system_prompt = "\n\n".join(system_messages) if system_messages else None

        user_messages = [m for m in messages if m["role"] != "system"]

        return self._anthropic_client.messages.create(
            model=model,
            system=system_prompt,
            messages=user_messages,
            max_tokens=kwargs.pop("max_tokens", 1024),
            **kwargs,
        )

    def _call_google(
        self, model: str, messages: list[dict[str, str]], **kwargs: Any
    ) -> Any:
        """Call Google Generative AI API.

        Args:
            model: Model name
            messages: Messages
            **kwargs: Additional arguments

        Returns:
            Google response

        Raises:
            ValueError: If Google AI not configured
        """
        if not hasattr(self, "_google_configured"):
            raise ValueError(
                "Google AI not configured. "
                "Pass google_api_key to KyrosProxy constructor."
            )

        if self.debug:
            print(f"[Kyros Debug] Calling Google AI with model: {model}")

        if genai is None:
            raise ValueError(
                "Google AI package is not available. "
                "Install it with: pip install google-generativeai"
            )

        model_obj = genai.GenerativeModel(model)

        # Convert messages to Gemini format
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")

        prompt = "\n\n".join(prompt_parts)

        return model_obj.generate_content(prompt, **kwargs)

    def close(self) -> None:
        """Close the Kyros client."""
        self.kyros.close()

    def __enter__(self) -> KyrosProxy:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()
