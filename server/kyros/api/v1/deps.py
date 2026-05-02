"""Shared API dependency helpers for v1 routes."""

from fastapi import Request

from kyros.services.memory_service import MemoryService
from kyros.storage.redis_cache import MemoryCache


def get_memory_service(request: Request) -> MemoryService:
    """Construct a MemoryService from app-scoped dependencies."""
    return MemoryService(
        embedder=request.app.state.embedder,
        cache=MemoryCache(request.app.state.redis),
    )
