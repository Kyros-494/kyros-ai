"""LangChain integration for Kyros persistent memory.

Requires: pip install langchain-core kyros-sdk
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyros import KyrosClient

from kyros.exceptions import KyrosError

try:
    from langchain_core.memory import BaseMemory  # type: ignore[import-not-found]
except ImportError as e:
    raise ImportError(
        "langchain-core is required for the LangChain integration. "
        "Install it with: pip install langchain-core"
    ) from e


class KyrosChatMemory(BaseMemory):  # type: ignore[misc]
    """Kyros-backed persistent memory for LangChain.

    Usage:
        from kyros import KyrosClient
        from kyros.integrations.langchain import KyrosChatMemory

        client = KyrosClient(api_key="mk_live_...")
        memory = KyrosChatMemory(client=client, agent_id="my-agent")

        chain = ConversationChain(llm=llm, memory=memory)
    """

    client: "KyrosClient"
    agent_id: str
    memory_key: str = "history"
    k: int = 10  # Number of memories to retrieve per turn

    class Config:
        arbitrary_types_allowed = True

    @property
    def memory_variables(self) -> list[str]:
        return [self.memory_key]

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Retrieve relevant memories based on the current input."""
        query = str(next(iter(inputs.values()), "")) if inputs else ""
        if not query:
            return {self.memory_key: ""}

        try:
            response = self.client.recall(self.agent_id, query, k=self.k)
            context = "\n".join(r.content for r in response.results)
        except KyrosError:
            context = ""

        return {self.memory_key: context}

    def save_context(self, inputs: dict[str, Any], outputs: dict[str, str]) -> None:
        """Store the conversation turn into Kyros."""
        user_msg = str(next(iter(inputs.values()), "")) if inputs else ""
        ai_msg = str(next(iter(outputs.values()), "")) if outputs else ""

        try:
            if user_msg:
                self.client.remember(self.agent_id, user_msg)
            if ai_msg:
                self.client.remember(self.agent_id, ai_msg)
        except KyrosError:
            pass  # Memory storage is best-effort — don't break the chain

    def clear(self) -> None:
        """No-op — use the admin API DELETE /v1/admin/agent/{agent_id}/memories for GDPR erasure."""
