"""CrewAI integration for Kyros persistent memory.

Requires: pip install crewai kyros-sdk
"""

from __future__ import annotations

from kyros import KyrosClient
from kyros.exceptions import KyrosError

try:
    from crewai.tools import BaseTool  # type: ignore[import-not-found]
    from pydantic import BaseModel, Field
except ImportError as e:
    raise ImportError(
        "crewai is required for the CrewAI integration. Install it with: pip install crewai"
    ) from e


class _RecallInput(BaseModel):
    query: str = Field(..., description="The query to search memories for")


class _RememberInput(BaseModel):
    fact: str = Field(..., description="The fact or observation to store")


class KyrosRecallTool(BaseTool):  # type: ignore[misc]
    """CrewAI tool for recalling relevant memories from Kyros."""

    name: str = "Recall Memory"
    description: str = (
        "Useful to recall past information, user preferences, decisions, or facts. "
        "Input should be a natural language query describing what you want to remember."
    )
    args_schema: type[BaseModel] = _RecallInput

    client: KyrosClient | None = None
    api_key: str | None = None
    base_url: str | None = None
    agent_id: str
    k: int = 10

    class Config:
        arbitrary_types_allowed = True

    def _run(self, query: str) -> str:
        try:
            client = self.client or KyrosClient(api_key=self.api_key, base_url=self.base_url)
            response = client.recall(self.agent_id, query, k=self.k)
            if not response.results:
                return "No relevant memories found."
            return "\n".join(f"- {r.content}" for r in response.results)
        except KyrosError as e:
            return f"Memory recall failed: {e!s}"


class KyrosRememberTool(BaseTool):  # type: ignore[misc]
    """CrewAI tool for storing new memories in Kyros."""

    name: str = "Store Memory"
    description: str = (
        "Useful to store an important fact, observation, or decision for future reference. "
        "Input should be the fact or observation to remember."
    )
    args_schema: type[BaseModel] = _RememberInput

    client: KyrosClient | None = None
    api_key: str | None = None
    base_url: str | None = None
    agent_id: str

    class Config:
        arbitrary_types_allowed = True

    def _run(self, fact: str) -> str:
        try:
            client = self.client or KyrosClient(api_key=self.api_key, base_url=self.base_url)
            client.remember(self.agent_id, fact)
            return "Memory successfully stored."
        except KyrosError as e:
            return f"Memory storage failed: {e!s}"


def get_kyros_tools(
    client: KyrosClient | None = None,
    agent_id: str | None = None,
    k: int = 10,
    api_key: str | None = None,
    base_url: str | None = None,
) -> list[BaseTool]:
    """Get a list of Kyros memory tools ready to pass to a CrewAI agent.

    Usage:
        from kyros.integrations.crewai import get_kyros_tools

        # Automatic configuration via environment variables:
        tools = get_kyros_tools(agent_id="my-crew-agent")

        agent = Agent(role="...", tools=tools)
    """
    if not agent_id:
        raise ValueError("agent_id must be provided")
    return [
        KyrosRecallTool(client=client, agent_id=agent_id, k=k, api_key=api_key, base_url=base_url),
        KyrosRememberTool(client=client, agent_id=agent_id, api_key=api_key, base_url=base_url),
    ]
