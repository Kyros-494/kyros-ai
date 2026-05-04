"""Kyros SDK type definitions — mirrors the server API schemas."""

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

# ─── Type Aliases ─────────────────────────────────────────────────────────────

MemoryType = Literal["episodic", "semantic", "procedural"]
ContentType = Literal["text", "action", "tool_call", "observation"]

# ─── Episodic Memory ──────────────────────────────────────────────────────────


class RememberResponse(BaseModel):
    """Response from storing an episodic memory."""

    memory_id: str
    agent_id: str
    memory_type: MemoryType
    created_at: str


class MemoryResult(BaseModel):
    """A single memory result from recall/search."""

    memory_id: str
    content: str
    memory_type: MemoryType
    relevance_score: float
    importance: float
    created_at: str
    metadata: Dict[str, Any]
    # Ebbinghaus decay fields (always present)
    freshness_score: float
    freshness_warning: bool
    memory_category: Optional[str] = None
    # Causal ancestry (present when include_causal_ancestry=True)
    causal_ancestry: List[Dict[str, Any]] = Field(default_factory=list)


class RecallResponse(BaseModel):
    """Response from recalling memories."""

    agent_id: str
    query: str
    results: List[MemoryResult]
    total_searched: int
    latency_ms: float


# ─── Semantic Memory ──────────────────────────────────────────────────────────


class FactResult(BaseModel):
    """Response from storing a semantic fact."""

    fact_id: str
    subject: str
    predicate: str
    object: str = Field(alias="object")  # 'object' is a Python keyword
    confidence: float
    created_at: str
    was_contradiction: bool
    replaced_fact_id: Optional[str] = None
    # Belief propagation updates triggered by this fact
    propagated_updates: List[Dict[str, Any]] = Field(default_factory=list)

    class Config:
        """Pydantic config."""

        populate_by_name = True  # Allow both 'object' and 'object' as field names


# ─── Procedural Memory ────────────────────────────────────────────────────────


class ProcedureResponse(BaseModel):
    """Response from storing a procedure."""

    procedure_id: str
    agent_id: str
    name: str
    task_type: str
    created_at: str


class ProcedureResult(BaseModel):
    """A single procedure result from matching."""

    procedure_id: str
    name: str
    description: str
    task_type: str
    steps: List[Dict[str, Any]]
    success_rate: float
    total_executions: int
    relevance_score: float
    avg_duration_ms: Optional[float] = None
    created_at: str


class ProcedureMatchResponse(BaseModel):
    """Response from matching procedures."""

    agent_id: str
    task_description: str
    results: List[ProcedureResult]
    latency_ms: float


class ProcedureOutcomeResponse(BaseModel):
    """Response from reporting procedure outcome."""

    procedure_id: str
    success_count: int
    failure_count: int
    success_rate: float
    avg_duration_ms: Optional[float] = None


# ─── Admin ────────────────────────────────────────────────────────────────────


class SummaryResponse(BaseModel):
    """Response from generating agent summary."""

    agent_id: str
    summary: str
    memory_count: int
    compression_ratio: float


class ExportData(BaseModel):
    """Exported memory data."""

    agent_id: str
    episodic: List[Dict[str, Any]]
    semantic: List[Dict[str, Any]]
    procedural: List[Dict[str, Any]]
    total_memories: int
    exported_at: str


# ─── Request Models (for type hints) ──────────────────────────────────────────


class RememberRequest(BaseModel):
    """Request to store episodic memory."""

    agent_id: str
    content: str
    content_type: ContentType = "text"
    role: Optional[str] = None
    session_id: Optional[str] = None
    importance: float = 0.5
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RecallRequest(BaseModel):
    """Request to recall memories."""

    agent_id: str
    query: str
    memory_type: Optional[MemoryType] = None
    k: int = 10
    min_relevance: float = 0.0
    session_id: Optional[str] = None
    include_causal_ancestry: bool = False


class StoreFactRequest(BaseModel):
    """Request to store semantic fact."""

    agent_id: str
    subject: str
    predicate: str
    object: str
    confidence: float = 1.0
    source_type: str = "explicit"


class StoreProcedureRequest(BaseModel):
    """Request to store procedure."""

    agent_id: str
    name: str
    description: str
    task_type: str
    steps: List[Dict[str, Any]]
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MatchProcedureRequest(BaseModel):
    """Request to match procedures."""

    agent_id: str
    task_description: str
    k: int = 5


class OutcomeRequest(BaseModel):
    """Request to report procedure outcome."""

    procedure_id: str
    success: bool
    duration_ms: Optional[int] = None
