"""Usage tracking middleware — logs every API operation to usage_events table.

Tracks latency and operation type for analytics and observability.
Uses fire-and-forget background tasks that are tracked by the global
task registry in main.py so they are properly cancelled on shutdown.
"""

from __future__ import annotations

import asyncio
import time
from uuid import uuid4

from sqlalchemy import text
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.usage")

OPERATION_MAP: dict[str, str] = {
    "/v1/memory/episodic/remember": "episodic.remember",
    "/v1/memory/episodic/recall": "episodic.recall",
    "/v1/memory/semantic/facts": "semantic.store_fact",
    "/v1/memory/semantic/query": "semantic.query",
    "/v1/memory/procedural/store": "procedural.store",
    "/v1/memory/procedural/match": "procedural.match",
    "/v1/memory/procedural/outcome": "procedural.outcome",
    "/v1/search/unified": "search.unified",
    "/v1/admin/summarise": "admin.summarise",
    "/v1/admin/export": "admin.export",
    "/v1/admin/import": "admin.import",
}

SKIP_PATHS: frozenset[str] = frozenset(
    {
        "/health",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


def _extract_memory_type(path: str) -> str | None:
    if "/episodic" in path:
        return "episodic"
    if "/semantic" in path:
        return "semantic"
    if "/procedural" in path:
        return "procedural"
    return None


def _resolve_operation(path: str, method: str) -> str | None:
    # Exact match first (O(1))
    op = OPERATION_MAP.get(path)
    if op:
        return op
    # Prefix match for paths with trailing segments (e.g. /v1/admin/summarise/agent-id)
    # Only check the known prefixes — avoids iterating the full map on every request
    if path.startswith("/v1/admin/"):
        for prefix in ("/v1/admin/summarise", "/v1/admin/export", "/v1/admin/import"):
            if path.startswith(prefix):
                return OPERATION_MAP.get(prefix)
    if "/episodic/" in path and method == "DELETE":
        return "episodic.forget"
    return None


async def _track(
    tenant_id: object,
    operation: str,
    memory_type: str | None,
    latency_ms: float,
    path: str,
) -> None:
    """Write a usage event row. Exceptions are logged, never re-raised."""
    try:
        async with get_db_session() as session:
            await session.execute(
                text("""
                INSERT INTO usage_events
                    (id, tenant_id, agent_id, operation, memory_type,
                     tokens_used, latency_ms, created_at)
                VALUES
                    (:id, :tenant_id, NULL, :operation, :memory_type,
                     0, :latency_ms, NOW())
                """),
                {
                    "id": uuid4(),
                    "tenant_id": tenant_id,
                    "operation": operation,
                    "memory_type": memory_type,
                    "latency_ms": latency_ms,
                },
            )
        logger.debug("Usage tracked", operation=operation, latency_ms=latency_ms)
    except Exception as e:
        logger.error(
            "Usage tracking failed",
            error=str(e),
            operation=operation,
            tenant_id=str(tenant_id),
            path=path,
        )


class UsageTrackingMiddleware(BaseHTTPMiddleware):
    """Logs every billable API operation to the usage_events table."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path
        method = request.method

        if path in SKIP_PATHS or path.startswith("/docs"):
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        if not tenant_id:
            return await call_next(request)

        start = time.monotonic()
        response = await call_next(request)
        latency_ms = round((time.monotonic() - start) * 1000, 2)

        operation = _resolve_operation(path, method)
        if operation:
            # Use the global tracked task registry if available (main.py)
            # Falls back to plain create_task if running outside the main app
            try:
                from kyros.main import create_background_task

                create_background_task(
                    _track(tenant_id, operation, _extract_memory_type(path), latency_ms, path)
                )
            except ImportError:
                task = asyncio.create_task(
                    _track(tenant_id, operation, _extract_memory_type(path), latency_ms, path)
                )
                task.add_done_callback(
                    lambda t: (
                        logger.error("Usage task failed", error=str(t.exception()))
                        if not t.cancelled() and t.exception()
                        else None
                    )
                )

        return response
