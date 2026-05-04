"""Kyros Python SDK.

Persistent memory operating system for AI agents.

Example:
    ```python
    from kyros import KyrosClient

    # Initialize client
    client = KyrosClient(api_key="your-api-key")

    # Store a memory
    response = client.remember(
        agent_id="agent-123",
        content="User prefers dark mode",
        importance=0.8
    )

    # Recall memories
    results = client.recall(
        agent_id="agent-123",
        query="What are the user's preferences?"
    )

    for memory in results.results:
        print(f"{memory.content} (score: {memory.relevance_score})")
    ```
"""

from .client import KyrosClient
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    KyrosError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError,
    ValidationError,
)
from .types import (
    ContentType,
    ExportData,
    FactResult,
    MemoryResult,
    MemoryType,
    ProcedureMatchResponse,
    ProcedureOutcomeResponse,
    ProcedureResponse,
    ProcedureResult,
    RecallResponse,
    RememberResponse,
    SummaryResponse,
)

__version__ = "0.1.0"

__all__ = [
    # Client
    "KyrosClient",
    # Exceptions
    "KyrosError",
    "AuthenticationError",
    "RateLimitError",
    "NotFoundError",
    "ValidationError",
    "ServerError",
    "TimeoutError",
    "ConnectionError",
    # Types
    "MemoryType",
    "ContentType",
    "RememberResponse",
    "RecallResponse",
    "MemoryResult",
    "FactResult",
    "ProcedureResponse",
    "ProcedureResult",
    "ProcedureMatchResponse",
    "ProcedureOutcomeResponse",
    "SummaryResponse",
    "ExportData",
]
