"""E16 — Create episodic_memories table with pgvector HNSW index

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Ensure pgvector extension exists
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "episodic_memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("role", sa.String(50), nullable=True),
        sa.Column("session_id", sa.String(255), nullable=True),
        sa.Column("embedding", Vector(384), nullable=False),
        # F01, F02: Dual Embeddings for Portability
        sa.Column("embedding_secondary", Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=False, server_default="all-MiniLM-L6-v2"),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("importance", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("compression_level", sa.Integer(), nullable=False, server_default="0"),
        # B01: Ebbinghaus Decay Engine columns
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("decay_rate", sa.Float(), nullable=False, server_default="0.02"),
        # B02: Memory category for domain-specific decay rates
        sa.Column("memory_category", sa.String(100), nullable=True, server_default="general"),
        # C01–C03: Memory Integrity Proof columns
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("merkle_leaf", sa.String(64), nullable=True),
        sa.Column("merkle_root", sa.String(64), nullable=True),
        sa.Column("nonce", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    # B-tree indexes for filtering
    op.create_index("ix_episodic_agent_created", "episodic_memories", ["agent_id", "created_at"])
    op.create_index("ix_episodic_session", "episodic_memories", ["agent_id", "session_id"])
    op.create_index("ix_episodic_tenant", "episodic_memories", ["tenant_id"])

    # Partial index for active (non-deleted) memories only
    op.execute("""
        CREATE INDEX ix_episodic_not_deleted
        ON episodic_memories (agent_id)
        WHERE deleted_at IS NULL
    """)

    # HNSW vector index for fast approximate nearest-neighbor search
    # m=16, ef_construction=200 gives excellent recall at reasonable build time
    op.execute("""
        CREATE INDEX ix_episodic_embedding_hnsw
        ON episodic_memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)


def downgrade() -> None:
    # Drop indexes first, then table
    op.execute("DROP INDEX IF EXISTS ix_episodic_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_episodic_not_deleted")
    op.drop_index("ix_episodic_tenant", "episodic_memories")
    op.drop_index("ix_episodic_session", "episodic_memories")
    op.drop_index("ix_episodic_agent_created", "episodic_memories")
    op.drop_table("episodic_memories")
