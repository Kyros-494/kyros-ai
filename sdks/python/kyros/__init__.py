"""Kyros Python SDK.

Persistent memory operating system for AI agents.

Example (Simple - Recommended):
    ```python
    from kyros import KyrosProxy

    # Initialize proxy with automatic memory management
    proxy = KyrosProxy(
        kyros_api_key="mk_live_...",
        openai_api_key="sk-...",
        debug=True
    )

    # One line - Kyros handles everything!
    response = proxy.chat(
        model="gpt-4",
        agent_id="user123",
        messages=[{"role": "user", "content": "What's my preference?"}]
    )

    print(response.choices[0].message.content)
    # → "You prefer dark mode" (from memory!)
    ```

Example (Advanced):
    ```python
    from kyros import KyrosClient

    # Initialize client for fine-grained control
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

# Debug and testing tools
from .debug import (
    DebugLogger,
    MemoryInspector,
    PerformanceProfiler,
    trace_memory_operation,
)
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
from .proxy import KyrosProxy
from .testing import (
    MemoryValidator,
    MockKyrosClient,
    TestDataGenerator,
    load_test_data,
    run_integration_test,
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
    "KyrosProxy",
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
    # Debug tools
    "MemoryInspector",
    "PerformanceProfiler",
    "DebugLogger",
    "trace_memory_operation",
    # Testing tools
    "TestDataGenerator",
    "MockKyrosClient",
    "MemoryValidator",
    "load_test_data",
    "run_integration_test",
]
