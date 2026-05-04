"""LlamaIndex integration for Kyros persistent memory.

Requires: pip install llama-index-core kyros-sdk
"""

from __future__ import annotations

from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from kyros import KyrosClient

from kyros.exceptions import KyrosError

try:
    from llama_index.core.llms import ChatMessage, MessageRole
    from llama_index.core.memory import BaseMemory
except ImportError as e:
    raise ImportError(
        "llama-index-core is required for the LlamaIndex integration. "
        "Install it with: pip install llama-index-core"
    ) from e


class KyrosMemory(BaseMemory):  # type: ignore[misc]
    """Kyros-backed persistent memory for LlamaIndex agents.

    Usage:
        from kyros import KyrosClient
        from kyros.integrations.llama_index import KyrosMemory

        client = KyrosClient(api_key="mk_live_...")
        memory = KyrosMemory.from_defaults(client=client, agent_id="my-agent")

        agent = ReActAgent.from_tools(tools, memory=memory)
    """

    client: "KyrosClient"
    agent_id: str
    k: int = 10

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def from_defaults(cls, client: "KyrosClient", agent_id: str, k: int = 10) -> "KyrosMemory":
        """Create a KyrosMemory instance with sensible defaults."""
        return cls(client=client, agent_id=agent_id, k=k)

    def get(self, input: str | None = None, **kwargs: Any) -> list[ChatMessage]:
        """Retrieve relevant memories as ChatMessage context."""
        if not input:
            return []

        try:
            response = self.client.recall(self.agent_id, input, k=self.k)
        except KyrosError:
            return []

        return [
            ChatMessage(
                role=MessageRole.SYSTEM,
                content=f"[Past Memory]: {r.content}",
            )
            for r in response.results
        ]

    def get_all(self) -> list[ChatMessage]:
        """Not supported — use recall() for semantic retrieval."""
        return []

    def put(self, message: ChatMessage) -> None:
        """Store a message as an episodic memory."""
        import contextlib

        content = message.content
        if not isinstance(content, str):
            content = str(content)
        if not content.strip():
            return

        with contextlib.suppress(KyrosError):
            self.client.remember(
                self.agent_id,
                content,
            )

    def set(self, messages: list[ChatMessage]) -> None:
        """Store a batch of messages."""
        for msg in messages:
            self.put(msg)

    def reset(self) -> None:
        """No-op — use the admin API DELETE /v1/admin/agent/{agent_id}/memories for GDPR erasure."""
