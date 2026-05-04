"""Pydantic schemas for Kyros API requests and responses."""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

# ─── Enums ─────────────────────────────────────


class MemoryType(StrEnum):
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"


class ContentType(StrEnum):
    TEXT = "text"
    ACTION = "action"
    TOOL_CALL = "tool_call"
    OBSERVATION = "observation"


# ─── REMEMBER (Write) ─────────────────────────


class RememberRequest(BaseModel):
    agent_id: str = Field(
        ..., min_length=1, max_length=255, description="Your agent's unique identifier"
    )
    content: str = Field(
        ..., min_length=1, max_length=50_000, description="Memory content to store"
    )
    memory_type: MemoryType = MemoryType.EPISODIC
    content_type: ContentType = ContentType.TEXT
    role: str | None = Field(default=None, max_length=50)
    session_id: str | None = Field(default=None, max_length=255)
    metadata: dict = Field(default_factory=dict)
    importance: float = Field(default=0.5, ge=0.0, le=1.0)
    # D07: Explicit Causal Edges
    cause_memory_id: str | None = Field(
        default=None, description="ID of the memory that caused this one"
    )
    effect_memory_id: str | None = Field(
        default=None, description="ID of the memory that this one caused"
    )

    @field_validator("content")
    @classmethod
    def content_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("content must not be blank or whitespace-only")
        return v

    @field_validator("agent_id")
    @classmethod
    def agent_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("agent_id must not be blank")
        return v.strip()


class RememberResponse(BaseModel):
    memory_id: UUID
    agent_id: str
    memory_type: MemoryType
    created_at: datetime


# ─── RECALL (Search) ──────────────────────────


class RecallRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    query: str = Field(
        ..., min_length=1, max_length=5_000, description="Natural language search query"
    )
    memory_type: MemoryType | None = None
    k: int = Field(default=10, ge=1, le=100, description="Number of results to return")
    min_relevance: float = Field(default=0.0, ge=0.0, le=1.0)
    session_id: str | None = Field(default=None, max_length=255)
    importance_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    freshness_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    # D10: Causal recall mode
    include_causal_ancestry: bool = Field(
        default=False,
        description="If true, fetches causal ancestors for each recalled memory",
    )

    @field_validator("query")
    @classmethod
    def query_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("query must not be blank")
        return v

    @field_validator("agent_id")
    @classmethod
    def agent_id_not_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("agent_id must not be blank")
        return v.strip()


class MemoryResult(BaseModel):
    memory_id: UUID
    content: str
    memory_type: MemoryType
    relevance_score: float
    importance: float
    created_at: datetime
    metadata: dict = Field(default_factory=dict)
    # B09: Ebbinghaus Decay Engine fields
    freshness_score: float = Field(default=1.0, ge=0.0, le=1.0)
    freshness_warning: bool = Field(default=False)
    memory_category: str | None = None
    # D10: Causal Ancestry — empty list instead of None for safer iteration
    causal_ancestry: list[dict] = Field(default_factory=list)


class RecallResponse(BaseModel):
    agent_id: str
    query: str
    results: list[MemoryResult]
    total_searched: int
    latency_ms: float


# ─── FORGET (Delete) ──────────────────────────


class ForgetRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    memory_id: UUID | None = None
    before: datetime | None = None
    memory_type: MemoryType | None = None


# ─── SUMMARISE ────────────────────────────────


class SummariseResponse(BaseModel):
    agent_id: str
    summary: str
    memory_count: int
    compression_ratio: float
    generated_at: datetime


# ─── SEMANTIC FACTS ───────────────────────────


class StoreFactRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    subject: str = Field(..., min_length=1, max_length=500, description="Entity the fact is about")
    predicate: str = Field(
        ..., min_length=1, max_length=500, description="Relationship or property name"
    )
    object: str = Field(..., min_length=1, max_length=5_000, description="Value of the fact")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    source_type: str = Field(default="explicit", max_length=50)


class FactResult(BaseModel):
    fact_id: UUID
    subject: str
    predicate: str
    object: str
    confidence: float
    created_at: datetime
    was_contradiction: bool = False
    replaced_fact_id: UUID | None = None
    # E10: Belief Propagation Report
    propagated_updates: list[dict] = Field(
        default_factory=list,
        description="Other facts whose confidence was updated due to this fact",
    )


# ─── PROCEDURAL MEMORY ────────────────────────


class StoreProcedureRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    name: str = Field(
        ..., min_length=1, max_length=500, description="Human-readable procedure name"
    )
    description: str = Field(
        ..., min_length=1, max_length=5_000, description="What this procedure does"
    )
    task_type: str = Field(
        ..., min_length=1, max_length=255, description="Task category for matching"
    )
    steps: list[dict] = Field(..., min_length=1, description="Ordered list of procedure steps")
    metadata: dict = Field(default_factory=dict)


class StoreProcedureResponse(BaseModel):
    procedure_id: UUID
    agent_id: str
    name: str
    task_type: str
    created_at: datetime


class MatchProcedureRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    task_description: str = Field(..., min_length=1, max_length=5_000)
    k: int = Field(default=5, ge=1, le=20)


class ProceduralResult(BaseModel):
    procedure_id: UUID
    name: str
    description: str
    task_type: str
    steps: list[dict]
    success_rate: float
    total_executions: int
    relevance_score: float
    avg_duration_ms: float | None
    created_at: datetime


class ProceduralMatchResponse(BaseModel):
    agent_id: str
    task_description: str
    results: list[ProceduralResult]
    latency_ms: float


class OutcomeRequest(BaseModel):
    procedure_id: UUID
    success: bool
    duration_ms: float | None = Field(default=None, ge=0.0)


class OutcomeResponse(BaseModel):
    procedure_id: UUID
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: float | None


# ─── EXPORT / IMPORT ─────────────────────────


class ExportResponse(BaseModel):
    agent_id: str
    episodic: list[dict]
    semantic: list[dict]
    procedural: list[dict]
    total_memories: int
    exported_at: datetime
