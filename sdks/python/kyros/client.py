"""Kyros Python SDK Client."""

from __future__ import annotations

from typing import Any

import httpx

from kyros.exceptions import KyrosAPIError, KyrosConnectionError
from kyros.types import (
    RecallRequest,
    RecallResponse,
    RememberRequest,
    RememberResponse,
)


class KyrosClient:
    """Kyros AI Memory System Client."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
    ) -> None:
        """Initialize Kyros client.

        Args:
            api_key: Your Kyros API key
            base_url: Base URL of Kyros server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json",
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Make HTTP request to Kyros API."""
        url = f"{self.base_url}{endpoint}"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    json=json,
                )
                response.raise_for_status()
                return response.json()  # type: ignore[no-any-return]
        except httpx.HTTPStatusError as e:
            raise KyrosAPIError(
                f"API error: {e.response.status_code} - {e.response.text}"
            ) from e
        except httpx.RequestError as e:
            raise KyrosConnectionError(f"Connection error: {e}") from e

    def remember(
        self,
        agent_id: str,
        content: str,
        importance: float = 0.5,
        session_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> RememberResponse:
        """Store a memory.

        Args:
            agent_id: Your agent's unique identifier
            content: Memory content to store
            importance: Importance score (0.0 to 1.0)
            session_id: Optional session identifier
            metadata: Optional metadata dictionary

        Returns:
            RememberResponse with memory_id and details
        """
        request = RememberRequest(
            agent_id=agent_id,
            content=content,
            importance=importance,
            session_id=session_id,
            metadata=metadata or {},
        )
        data = self._request("POST", "/v1/memory/episodic/remember", request.model_dump())
        return RememberResponse(**data)

    def recall(
        self,
        agent_id: str,
        query: str,
        k: int = 10,
        session_id: str | None = None,
    ) -> RecallResponse:
        """Recall memories.

        Args:
            agent_id: Your agent's unique identifier
            query: Natural language search query
            k: Number of results to return
            session_id: Optional session filter

        Returns:
            RecallResponse with matching memories
        """
        request = RecallRequest(
            agent_id=agent_id,
            query=query,
            k=k,
            session_id=session_id,
        )
        data = self._request("POST", "/v1/memory/episodic/recall", request.model_dump())
        return RecallResponse(**data)

    def forget(self, memory_id: str) -> None:
        """Delete a memory.

        Args:
            memory_id: ID of memory to delete
        """
        self._request("DELETE", f"/v1/memory/episodic/{memory_id}")

    def health(self) -> dict[str, Any]:
        """Check server health.

        Returns:
            Health status dictionary
        """
        return self._request("GET", "/health")
