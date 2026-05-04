"""Kyros SDK Types."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class MemoryType(str, Enum):
    """Memory type enumeration."""

    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ContentType(str, Enum):
    """Content type enumeration."""

    TEXT = "text"
    CODE = "code"
    JSON = "json"


class RememberRequest(BaseModel):
    """Request to store a memory."""

    agent_id: str = Field(..., min_length=1, max_length=255)
    content: str = Field(..., min_length=1, max_length=50_000)
    memory_type: MemoryType = MemoryType.EPISODIC
    content_type: ContentType = ContentType.TEXT
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RememberResponse(BaseModel):
    """Response from storing a memory."""

    memory_id: str
    agent_id: str
    memory_type: str
    created_at: datetime


class RecallRequest(BaseModel):
    """Request to recall memories."""

    agent_id: str = Field(..., min_length=1, max_length=255)
    query: str = Field(..., min_length=1, max_length=5_000)
    memory_type: MemoryType | None = None
    k: int = Field(default=10, ge=1, le=100)
    session_id: str | None = None


class MemoryResult(BaseModel):
    """A single memory result."""

    memory_id: str
    content: str
    similarity: float
    importance: float
    created_at: datetime
    session_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecallResponse(BaseModel):
    """Response from recalling memories."""

    results: list[MemoryResult]
    query: str
    total_results: int
