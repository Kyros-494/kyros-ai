"""Kyros Python SDK Client.

Mirrors the TypeScript SDK API surface using httpx.
"""

import os
from typing import Any, cast

import httpx

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
    MemoryType,
    ProcedureMatchResponse,
    ProcedureOutcomeResponse,
    ProcedureResponse,
    RecallResponse,
    RememberResponse,
    SummaryResponse,
)


class KyrosClient:
    """Kyros API client for Python.

    Example:
        ```python
        from kyros import KyrosClient

        client = KyrosClient(api_key="your-api-key")

        # Store a memory
        response = client.remember(
            agent_id="agent-123",
            content="User prefers dark mode"
        )

        # Recall memories
        results = client.recall(
            agent_id="agent-123",
            query="What are the user's preferences?"
        )
        ```
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: float = 30.0,
    ) -> None:
        """Initialize Kyros client.

        Args:
            api_key: API key for authentication. If not provided, reads from
                KYROS_API_KEY environment variable.
            base_url: Base URL for Kyros API. Defaults to https://api.kyros.ai
                or KYROS_BASE_URL environment variable.
            timeout: Request timeout in seconds. Defaults to 30.0.

        Raises:
            AuthenticationError: If no API key is provided.
        """
        self.api_key = api_key or os.getenv("KYROS_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "No API key provided. Pass api_key parameter or set "
                "KYROS_API_KEY environment variable."
            )

        self.base_url = (base_url or os.getenv("KYROS_BASE_URL") or "https://api.kyros.ai").rstrip(
            "/"
        )
        self.timeout = timeout

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
                "User-Agent": "kyros-sdk-python/0.1.0",
            },
            timeout=timeout,
        )

    def __enter__(self) -> "KyrosClient":
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()

    def close(self) -> None:
        """Close the HTTP client."""
        self._client.close()

    def _request(
        self,
        method: str,
        path: str,
        json: dict[str, Any] | None = None,
    ) -> Any:
        """Make HTTP request to Kyros API.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            path: API endpoint path
            json: Request body (for POST/PUT)

        Returns:
            Response data (parsed JSON)

        Raises:
            KyrosError: On API errors
            TimeoutError: On request timeout
            ConnectionError: On connection failure
        """
        try:
            response = self._client.request(method, path, json=json)
            return self._handle_response(response)
        except httpx.TimeoutException as e:
            raise TimeoutError(
                f"Request timed out after {self.timeout}s",
                timeout=self.timeout,
            ) from e
        except httpx.ConnectError as e:
            raise ConnectionError(
                f"Failed to connect to {self.base_url}",
                base_url=self.base_url,
            ) from e
        except httpx.HTTPError as e:
            raise KyrosError(f"HTTP error: {e}") from e

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle HTTP response and raise appropriate exceptions.

        Args:
            response: HTTP response object

        Returns:
            Parsed JSON response data

        Raises:
            AuthenticationError: On 401/403
            NotFoundError: On 404
            ValidationError: On 422
            RateLimitError: On 429
            ServerError: On 5xx
            KyrosError: On other errors
        """
        if response.status_code == 204:
            return None

        # Try to parse error body
        try:
            body = response.json()
        except Exception:
            body = {"message": response.text}

        message = body.get("message") or body.get("detail") or f"HTTP {response.status_code}"
        error_code = body.get("error")

        if response.status_code in (401, 403):
            raise AuthenticationError(message, response.status_code, error_code)
        elif response.status_code == 404:
            raise NotFoundError(message, error_code)
        elif response.status_code == 422:
            raise ValidationError(message, error_code)
        elif response.status_code == 429:
            limit = int(response.headers.get("X-RateLimit-Limit", 0))
            remaining = int(response.headers.get("X-RateLimit-Remaining", 0))
            reset_at = int(response.headers.get("X-RateLimit-Reset", 0))
            raise RateLimitError(message, limit, remaining, reset_at, error_code)
        elif response.status_code >= 500:
            raise ServerError(message, response.status_code, error_code)
        elif not response.is_success:
            raise KyrosError(message, response.status_code, error_code)

        return body

    # ─── Episodic Memory ──────────────────────────────────────────────────────

    def remember(
        self,
        agent_id: str,
        content: str,
        content_type: ContentType = "text",
        role: str | None = None,
        session_id: str | None = None,
        importance: float = 0.5,
        metadata: dict[str, Any] | None = None,
    ) -> RememberResponse:
        """Store an episodic memory.

        Args:
            agent_id: Unique identifier for the agent
            content: Memory content (text, action, observation, etc.)
            content_type: Type of content (text, action, tool_call, observation)
            role: Role of the speaker (user, assistant, system, etc.)
            session_id: Session identifier for grouping related memories
            importance: Importance score (0.0 to 1.0)
            metadata: Additional metadata as key-value pairs

        Returns:
            RememberResponse with memory_id and metadata

        Example:
            ```python
            response = client.remember(
                agent_id="agent-123",
                content="User prefers dark mode",
                importance=0.8,
                metadata={"category": "preferences"}
            )
            print(response.memory_id)
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/episodic/remember",
            json={
                "agent_id": agent_id,
                "content": content,
                "content_type": content_type,
                "role": role,
                "session_id": session_id,
                "importance": importance,
                "metadata": metadata or {},
            },
        )
        return RememberResponse(**data)

    def recall(
        self,
        agent_id: str,
        query: str,
        memory_type: MemoryType | None = None,
        k: int = 10,
        min_relevance: float = 0.0,
        session_id: str | None = None,
        include_causal_ancestry: bool = False,
    ) -> RecallResponse:
        """Recall memories using semantic search.

        Args:
            agent_id: Unique identifier for the agent
            query: Search query
            memory_type: Filter by memory type (episodic, semantic, procedural)
            k: Number of results to return
            min_relevance: Minimum relevance score (0.0 to 1.0)
            session_id: Filter by session ID
            include_causal_ancestry: Include causal ancestry chain (adds latency)

        Returns:
            RecallResponse with list of matching memories

        Example:
            ```python
            results = client.recall(
                agent_id="agent-123",
                query="What are the user's preferences?",
                k=5
            )
            for memory in results.results:
                print(f"{memory.content} (score: {memory.relevance_score})")
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/episodic/recall",
            json={
                "agent_id": agent_id,
                "query": query,
                "memory_type": memory_type,
                "k": k,
                "min_relevance": min_relevance,
                "session_id": session_id,
                "include_causal_ancestry": include_causal_ancestry,
            },
        )
        return RecallResponse(**data)

    def forget(self, agent_id: str, memory_id: str) -> None:
        """Delete a memory (soft delete).

        Args:
            agent_id: Unique identifier for the agent (for API symmetry)
            memory_id: Memory ID to delete

        Example:
            ```python
            client.forget(agent_id="agent-123", memory_id="mem-456")
            ```
        """
        self._request("DELETE", f"/v1/memory/episodic/{memory_id}")

    # ─── Semantic Memory ──────────────────────────────────────────────────────

    def store_fact(
        self,
        agent_id: str,
        subject: str,
        predicate: str,
        value: str,
        confidence: float = 1.0,
        source_type: str = "explicit",
    ) -> FactResult:
        """Store a semantic fact (subject-predicate-object triple).

        Args:
            agent_id: Unique identifier for the agent
            subject: Subject of the fact
            predicate: Predicate (relationship)
            value: Object (value)
            confidence: Confidence score (0.0 to 1.0)
            source_type: Source type (explicit, inferred, etc.)

        Returns:
            FactResult with fact_id and metadata

        Example:
            ```python
            fact = client.store_fact(
                agent_id="agent-123",
                subject="user",
                predicate="prefers",
                value="dark mode",
                confidence=0.9
            )
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/semantic/facts",
            json={
                "agent_id": agent_id,
                "subject": subject,
                "predicate": predicate,
                "object": value,
                "confidence": confidence,
                "source_type": source_type,
            },
        )
        return FactResult(**data)

    def query_facts(
        self,
        agent_id: str,
        query: str,
        k: int = 10,
    ) -> RecallResponse:
        """Query semantic facts.

        Args:
            agent_id: Unique identifier for the agent
            query: Search query
            k: Number of results to return

        Returns:
            RecallResponse with matching facts

        Example:
            ```python
            results = client.query_facts(
                agent_id="agent-123",
                query="user preferences"
            )
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/semantic/query",
            json={
                "agent_id": agent_id,
                "query": query,
                "k": k,
            },
        )
        return RecallResponse(**data)

    # ─── Procedural Memory ────────────────────────────────────────────────────

    def store_procedure(
        self,
        agent_id: str,
        name: str,
        description: str,
        task_type: str,
        steps: list[dict[str, Any]],
        metadata: dict[str, Any] | None = None,
    ) -> ProcedureResponse:
        """Store a procedure (workflow, skill, etc.).

        Args:
            agent_id: Unique identifier for the agent
            name: Procedure name
            description: Procedure description
            task_type: Type of task
            steps: List of steps (each step is a dict)
            metadata: Additional metadata

        Returns:
            ProcedureResponse with procedure_id

        Example:
            ```python
            procedure = client.store_procedure(
                agent_id="agent-123",
                name="Send Email",
                description="Send an email to a recipient",
                task_type="communication",
                steps=[
                    {"action": "compose", "params": {"to": "user@example.com"}},
                    {"action": "send"}
                ]
            )
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/procedural/store",
            json={
                "agent_id": agent_id,
                "name": name,
                "description": description,
                "task_type": task_type,
                "steps": steps,
                "metadata": metadata or {},
            },
        )
        return ProcedureResponse(**data)

    def match_procedure(
        self,
        agent_id: str,
        task_description: str,
        k: int = 5,
    ) -> ProcedureMatchResponse:
        """Find matching procedures for a task.

        Args:
            agent_id: Unique identifier for the agent
            task_description: Description of the task
            k: Number of results to return

        Returns:
            ProcedureMatchResponse with matching procedures

        Example:
            ```python
            matches = client.match_procedure(
                agent_id="agent-123",
                task_description="I need to send an email"
            )
            for proc in matches.results:
                print(f"{proc.name}: {proc.success_rate}")
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/procedural/match",
            json={
                "agent_id": agent_id,
                "task_description": task_description,
                "k": k,
            },
        )
        return ProcedureMatchResponse(**data)

    def report_outcome(
        self,
        procedure_id: str,
        success: bool,
        duration_ms: int | None = None,
    ) -> ProcedureOutcomeResponse:
        """Report the outcome of a procedure execution.

        Args:
            procedure_id: Procedure ID
            success: Whether execution was successful
            duration_ms: Execution duration in milliseconds

        Returns:
            ProcedureOutcomeResponse with updated statistics

        Example:
            ```python
            outcome = client.report_outcome(
                procedure_id="proc-456",
                success=True,
                duration_ms=1500
            )
            print(f"Success rate: {outcome.success_rate}")
            ```
        """
        data = self._request(
            "POST",
            "/v1/memory/procedural/outcome",
            json={
                "procedure_id": procedure_id,
                "success": success,
                "duration_ms": duration_ms,
            },
        )
        return ProcedureOutcomeResponse(**data)

    # ─── Admin ────────────────────────────────────────────────────────────────

    def summarise(self, agent_id: str) -> SummaryResponse:
        """Generate a summary of agent's memories.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            SummaryResponse with summary text and statistics

        Example:
            ```python
            summary = client.summarise(agent_id="agent-123")
            print(summary.summary)
            ```
        """
        data = self._request("GET", f"/v1/admin/summarise/{agent_id}")
        return SummaryResponse(**data)

    def export_memories(self, agent_id: str) -> ExportData:
        """Export all memories for an agent.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            ExportData with all memories

        Example:
            ```python
            export = client.export_memories(agent_id="agent-123")
            print(f"Exported {export.total_memories} memories")
            ```
        """
        data = self._request("GET", f"/v1/admin/export/{agent_id}")
        return ExportData(**data)

    def import_memories(
        self,
        agent_id: str,
        data: ExportData,
    ) -> dict[str, Any]:
        """Import memories for an agent.

        Args:
            agent_id: Unique identifier for the agent
            data: Export data to import

        Returns:
            Import result with statistics

        Example:
            ```python
            export = client.export_memories(agent_id="agent-123")
            result = client.import_memories(agent_id="agent-456", data=export)
            ```
        """
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"/v1/admin/import/{agent_id}",
                json=data.model_dump(),
            ),
        )

    # ─── Unified Search ───────────────────────────────────────────────────────

    def search(
        self,
        agent_id: str,
        query: str,
        k: int = 10,
    ) -> RecallResponse:
        """Search across all memory types.

        Args:
            agent_id: Unique identifier for the agent
            query: Search query
            k: Number of results to return

        Returns:
            RecallResponse with results from all memory types

        Example:
            ```python
            results = client.search(
                agent_id="agent-123",
                query="email preferences"
            )
            ```
        """
        data = self._request(
            "POST",
            "/v1/search/unified",
            json={
                "agent_id": agent_id,
                "query": query,
                "k": k,
            },
        )
        return RecallResponse(**data)

    # ─── Advanced Features ────────────────────────────────────────────────────

    def get_staleness_report(self, agent_id: str) -> dict[str, Any]:
        """Get staleness report for agent's memories.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Staleness report with decay statistics
        """
        return cast(
            dict[str, Any],
            self._request("GET", f"/v1/admin/staleness-report/{agent_id}"),
        )

    def get_decay_rates(self) -> dict[str, Any]:
        """Get current decay rates for memory categories.

        Returns:
            Decay rates configuration
        """
        return cast(dict[str, Any], self._request("GET", "/v1/admin/decay-rates"))

    def set_decay_rates(self, rates: dict[str, float]) -> dict[str, Any]:
        """Set decay rates for memory categories.

        Args:
            rates: Decay rates by category

        Returns:
            Updated decay rates configuration
        """
        return cast(
            dict[str, Any],
            self._request("PUT", "/v1/admin/decay-rates", json={"rates": rates}),
        )

    def get_memory_proof(self, memory_id: str) -> dict[str, Any]:
        """Get cryptographic integrity proof for a memory.

        Args:
            memory_id: Memory ID

        Returns:
            Integrity proof with hash and Merkle tree data
        """
        return cast(
            dict[str, Any],
            self._request("GET", f"/v1/admin/memory/{memory_id}/proof"),
        )

    def audit_integrity(self, agent_id: str) -> dict[str, Any]:
        """Audit integrity of all memories for an agent.

        Args:
            agent_id: Unique identifier for the agent

        Returns:
            Audit report with verification results
        """
        return cast(
            dict[str, Any],
            self._request("POST", f"/v1/admin/agent/{agent_id}/audit"),
        )

    def explain(
        self,
        agent_id: str,
        memory_id: str,
        max_depth: int = 3,
    ) -> dict[str, Any]:
        """Get causal explanation for a memory.

        Args:
            agent_id: Unique identifier for the agent
            memory_id: Memory ID to explain
            max_depth: Maximum depth of causal chain

        Returns:
            Causal explanation with ancestry chain
        """
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                "/v1/memory/causal/explain",
                json={
                    "agent_id": agent_id,
                    "memory_id": memory_id,
                    "max_depth": max_depth,
                    "direction": "causes",
                },
            ),
        )

    def migrate_embeddings(
        self,
        agent_id: str,
        from_model: str,
        to_model: str,
        strategy: str = "translate",
    ) -> dict[str, Any]:
        """Migrate embeddings from one model to another.

        Args:
            agent_id: Unique identifier for the agent
            from_model: Source embedding model
            to_model: Target embedding model
            strategy: Migration strategy (translate or re-embed)

        Returns:
            Migration result with statistics
        """
        return cast(
            dict[str, Any],
            self._request(
                "POST",
                f"/v1/admin/agent/{agent_id}/migrate-embeddings",
                json={
                    "from_model": from_model,
                    "to_model": to_model,
                    "strategy": strategy,
                },
            ),
        )
