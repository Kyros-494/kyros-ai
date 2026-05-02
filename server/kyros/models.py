"""SQLAlchemy ORM models for Kyros.

All models inherit from Base and are auto-discovered by Alembic for migrations.
"""

from uuid import uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    func,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    """Base class for all Kyros ORM models."""
    pass


# ─── E15: Tenants & Agents ────────────────────

class Tenant(Base):
    """A tenant (organisation or individual user) — the billing unit."""
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(255), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    api_key_hash = Column(String(255), nullable=False, unique=True)
    plan = Column(String(50), nullable=False, default="free")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    agents = relationship("Agent", back_populates="tenant", cascade="all, delete-orphan")
    usage_events = relationship("UsageEvent", back_populates="tenant", cascade="all, delete-orphan")


class Agent(Base):
    """An AI agent that stores memories — belongs to a tenant."""
    __tablename__ = "agents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    external_id = Column(String(255), nullable=False)
    display_name = Column(String(255), nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("tenant_id", "external_id", name="uq_agent_tenant_external"),
    )

    tenant = relationship("Tenant", back_populates="agents")
    episodic_memories = relationship("EpisodicMemory", back_populates="agent", cascade="all, delete-orphan")
    semantic_memories = relationship("SemanticMemory", back_populates="agent", cascade="all, delete-orphan")
    procedural_memories = relationship("ProceduralMemory", back_populates="agent", cascade="all, delete-orphan")


# ─── E16: Episodic Memories ───────────────────

class EpisodicMemory(Base):
    """A single episodic memory — a conversation turn, action, or observation."""
    __tablename__ = "episodic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    content = Column(Text, nullable=False)
    content_type = Column(String(50), nullable=False, default="text")
    role = Column(String(50), nullable=True)
    session_id = Column(String(255), nullable=True)
    embedding = Column(Vector(384), nullable=False)
    
    # F01, F02: Dual Embeddings for Portability
    embedding_secondary = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=False, default="all-MiniLM-L6-v2")
    
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    importance = Column(Float, nullable=False, default=0.5)
    compression_level = Column(Integer, nullable=False, default=0)
    # B01: Ebbinghaus Decay Engine columns
    freshness_score = Column(Float, nullable=False, default=1.0)
    decay_rate = Column(Float, nullable=False, default=0.02)
    # B02: Memory category for domain-specific decay rates
    memory_category = Column(String(100), nullable=True, default="general")
    # C01–C03: Memory Integrity Proof columns
    content_hash = Column(String(64), nullable=True)      # SHA-256 of content+metadata
    merkle_leaf = Column(String(64), nullable=True)        # This memory's Merkle leaf hash
    merkle_root = Column(String(64), nullable=True)        # Current Merkle root at write time
    nonce = Column(String(32), nullable=True)              # Random nonce to prevent hash collisions
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_episodic_agent_created", "agent_id", "created_at"),
        Index("ix_episodic_session", "agent_id", "session_id"),
        Index("ix_episodic_tenant", "tenant_id"),
        Index("ix_episodic_not_deleted", "agent_id", postgresql_where="deleted_at IS NULL"),
    )

    agent = relationship("Agent", back_populates="episodic_memories")


# ─── E17: Semantic Memories ───────────────────

class SemanticMemory(Base):
    """A semantic fact — subject-predicate-object triple (knowledge graph)."""
    __tablename__ = "semantic_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    subject = Column(String(500), nullable=False)
    predicate = Column(String(500), nullable=False)
    object = Column(Text, nullable=False)
    confidence = Column(Float, nullable=False, default=1.0)
    embedding = Column(Vector(384), nullable=False)
    
    # F01, F02: Dual Embeddings for Portability
    embedding_secondary = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=False, default="all-MiniLM-L6-v2")
    
    source_type = Column(String(50), nullable=False, default="explicit")
    # B01: Ebbinghaus Decay Engine columns
    freshness_score = Column(Float, nullable=False, default=1.0)
    decay_rate = Column(Float, nullable=False, default=0.005)
    # B02: Memory category for domain-specific decay rates
    memory_category = Column(String(100), nullable=True, default="fact")
    # C01–C03: Memory Integrity Proof columns
    content_hash = Column(String(64), nullable=True)
    merkle_leaf = Column(String(64), nullable=True)
    merkle_root = Column(String(64), nullable=True)
    nonce = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_semantic_agent_subject", "agent_id", "subject"),
        Index("ix_semantic_agent_spo", "agent_id", "subject", "predicate"),
        Index("ix_semantic_tenant", "tenant_id"),
        Index("ix_semantic_not_deleted", "agent_id", postgresql_where="deleted_at IS NULL"),
    )

    agent = relationship("Agent", back_populates="semantic_memories")


# ─── E18: Procedural Memories ─────────────────

class ProceduralMemory(Base):
    """A learned procedure — a reusable workflow or tool-call sequence."""
    __tablename__ = "procedural_memories"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    task_type = Column(String(255), nullable=False)
    steps = Column(JSONB, nullable=False)
    embedding = Column(Vector(384), nullable=False)
    
    # F01, F02: Dual Embeddings for Portability
    embedding_secondary = Column(Vector(1536), nullable=True)
    embedding_model = Column(String(100), nullable=False, default="all-MiniLM-L6-v2")
    
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    avg_duration_ms = Column(Float, nullable=True)
    metadata_ = Column("metadata", JSONB, nullable=False, default=dict)
    # B01: Ebbinghaus Decay Engine columns
    freshness_score = Column(Float, nullable=False, default=1.0)
    decay_rate = Column(Float, nullable=False, default=0.01)
    # B02: Memory category for domain-specific decay rates
    memory_category = Column(String(100), nullable=True, default="workflow")
    # C01–C03: Memory Integrity Proof columns
    content_hash = Column(String(64), nullable=True)
    merkle_leaf = Column(String(64), nullable=True)
    merkle_root = Column(String(64), nullable=True)
    nonce = Column(String(32), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("ix_procedural_agent_task", "agent_id", "task_type"),
        Index("ix_procedural_tenant", "tenant_id"),
        Index("ix_procedural_not_deleted", "agent_id", postgresql_where="deleted_at IS NULL"),
    )

    agent = relationship("Agent", back_populates="procedural_memories")


# ─── E19: Usage Events ────────────────────────

class UsageEvent(Base):
    """A billing usage event — every API operation is logged here."""
    __tablename__ = "usage_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(UUID(as_uuid=True), nullable=True)
    operation = Column(String(100), nullable=False)
    memory_type = Column(String(50), nullable=True)
    tokens_used = Column(Integer, nullable=False, default=0)
    latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_usage_tenant_created", "tenant_id", "created_at"),
        Index("ix_usage_tenant_op", "tenant_id", "operation"),
    )

    tenant = relationship("Tenant", back_populates="usage_events")


# ─── C07: Memory Audit Log ────────────────────

class MemoryAuditLog(Base):
    """Append-only audit log for cryptographic Merkle roots.
    
    Used to prove the state of an agent's memory at any given point in time.
    Provides immutable evidence of memory integrity.
    """
    __tablename__ = "memory_audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    merkle_root = Column(String(64), nullable=False)
    tree_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_audit_agent_created", "agent_id", "created_at"),
        Index("ix_audit_tenant", "tenant_id"),
    )

    agent = relationship("Agent")


# ─── D01: Causal Memory Graph ─────────────────

class CausalEdge(Base):
    """A causal relationship between two memories (WHY something happened).
    
    Creates a directed graph of memories: from_memory_id -(relation)-> to_memory_id.
    Usually: cause -(causes)-> effect, or decision -(based_on)-> observation.
    """
    __tablename__ = "causal_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    # We use String/UUID for from/to because they can point to any memory table
    # (episodic, semantic, procedural)
    from_memory_id = Column(UUID(as_uuid=True), nullable=False)
    to_memory_id = Column(UUID(as_uuid=True), nullable=False)
    
    relation = Column(String(100), nullable=False, default="causes")  # 'causes', 'motivates', 'prevents'
    confidence = Column(Float, nullable=False, default=1.0)
    description = Column(Text, nullable=True)  # Human-readable explanation of the causality
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_causal_agent", "agent_id"),
        Index("ix_causal_from", "from_memory_id"),
        Index("ix_causal_to", "to_memory_id"),
        UniqueConstraint("from_memory_id", "to_memory_id", "relation", name="uq_causal_edge"),
    )

    agent = relationship("Agent")


# ─── E04: Semantic Belief Graph ───────────────

class SemanticEdge(Base):
    """A semantic relationship between two facts in semantic memory.
    
    Used for Belief Propagation: if the confidence of from_fact changes,
    the confidence of to_fact is automatically updated based on their relatedness.
    """
    __tablename__ = "semantic_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False)
    
    from_fact_id = Column(UUID(as_uuid=True), ForeignKey("semantic_memories.id", ondelete="CASCADE"), nullable=False)
    to_fact_id = Column(UUID(as_uuid=True), ForeignKey("semantic_memories.id", ondelete="CASCADE"), nullable=False)
    
    # Cosine similarity between the embeddings of the two facts
    relatedness_score = Column(Float, nullable=False)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_sem_edge_agent", "agent_id"),
        Index("ix_sem_edge_from", "from_fact_id"),
        Index("ix_sem_edge_to", "to_fact_id"),
        UniqueConstraint("from_fact_id", "to_fact_id", name="uq_semantic_edge"),
    )

    agent = relationship("Agent")
    from_fact = relationship("SemanticMemory", foreign_keys=[from_fact_id])
    to_fact = relationship("SemanticMemory", foreign_keys=[to_fact_id])


# ─── E11: Propagation Audit Log ───────────────

class SemanticPropagationLog(Base):
    """Audit log of all confidence changes caused by belief propagation."""
    __tablename__ = "semantic_propagation_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False)
    
    fact_id = Column(UUID(as_uuid=True), ForeignKey("semantic_memories.id", ondelete="CASCADE"), nullable=False)
    triggered_by_fact_id = Column(UUID(as_uuid=True), nullable=False)
    
    old_confidence = Column(Float, nullable=False)
    new_confidence = Column(Float, nullable=False)
    depth = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, nullable=False, server_default=func.now())

    __table_args__ = (
        Index("ix_sem_prop_log_agent", "agent_id"),
        Index("ix_sem_prop_log_fact", "fact_id"),
    )




    agent = relationship("Agent")
    fact = relationship("SemanticMemory", foreign_keys=[fact_id])
