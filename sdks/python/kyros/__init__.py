"""Kyros Python SDK - AI Memory System Client."""

from kyros.client import KyrosClient
from kyros.exceptions import KyrosAPIError, KyrosConnectionError, KyrosError
from kyros.types import (
    ContentType,
    MemoryResult,
    MemoryType,
    RecallRequest,
    RecallResponse,
    RememberRequest,
    RememberResponse,
)

__version__ = "0.1.0"

# Alias for backward compatibility
Client = KyrosClient

__all__ = [
    "KyrosClient",
    "Client",
    "KyrosError",
    "KyrosAPIError",
    "KyrosConnectionError",
    "MemoryType",
    "ContentType",
    "RememberRequest",
    "RememberResponse",
    "RecallRequest",
    "RecallResponse",
    "MemoryResult",
]
