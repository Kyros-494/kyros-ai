"""AutoGen integration for Kyros persistent memory.

Requires: pip install pyautogen kyros-sdk
"""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from kyros import KyrosClient

from kyros.exceptions import KyrosError


def inject_kyros_memory(agent: Any, client: "KyrosClient", agent_id: str, k: int = 10) -> None:
    """Wrap an AutoGen agent to automatically store and recall messages using Kyros.

    Patches the agent's `receive` method to:
    1. Recall relevant memories before processing each message
    2. Inject them as context into the message
    3. Store the incoming message as a new episodic memory

    Usage:
        import autogen
        from kyros import KyrosClient
        from kyros.integrations.autogen import inject_kyros_memory

        client = KyrosClient(api_key="mk_live_...")
        agent = autogen.AssistantAgent("assistant", llm_config=llm_config)
        inject_kyros_memory(agent, client, agent_id="my-autogen-agent")

    Args:
        agent: An AutoGen ConversableAgent instance.
        client: Kyros Client instance.
        agent_id: The agent ID to scope memories to.
        k: Number of memories to inject per turn (default 10).
    """
    original_receive = agent.receive

    def receive_with_memory(
        message: str | dict[str, Any],
        sender: Any,
        request_reply: bool | None = None,
        silent: bool | None = False,
    ) -> Any:
        # Extract text content from message
        query = str(message.get("content", "")) if isinstance(message, dict) else str(message)

        # Recall relevant memories and inject as context
        if query.strip():
            try:
                response = client.recall(agent_id, query, k=k)
                if response.results:
                    context = "\n".join(f"- {r.content}" for r in response.results)
                    memory_injection = (
                        f"\n\n[Kyros Persistent Memory Context]:\n{context}\n"
                        f"[End of memory context]\n"
                    )
                    if isinstance(message, dict):
                        content = message.get("content", "")
                        message = {**message, "content": content + memory_injection}
                    else:
                        message = message + memory_injection
            except KyrosError:
                pass  # Memory recall is best-effort — don't break the agent

            # Store incoming message as episodic memory
            with contextlib.suppress(KyrosError):
                client.remember(agent_id, query)

        return original_receive(message, sender, request_reply, silent)

    agent.receive = receive_with_memory
