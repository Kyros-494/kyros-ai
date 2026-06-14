"""Shared API dependency helpers for v1 routes."""

from fastapi import Request

from kyros.services.memory_service import MemoryService
from kyros.storage.redis_cache import MemoryCache


def get_memory_service(request: Request) -> MemoryService:
    """Construct a MemoryService from app-scoped dependencies."""
    service = MemoryService(
        embedder=request.app.state.embedder,
        cache=MemoryCache(request.app.state.redis),
    )
    # Extract custom embedding model overrides from headers or query parameters
    emb_model = request.headers.get("X-Embedding-Model") or request.query_params.get("embedding_model")
    if emb_model:
        service.override_embedding_model = emb_model
    return service
