"""E17 — Create semantic_memories table with indexes

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-25
"""
from collections.abc import Sequence

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "semantic_memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(500), nullable=False),
        sa.Column("predicate", sa.String(500), nullable=False),
        sa.Column("object", sa.Text(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("embedding", Vector(384), nullable=False),
        # F01, F02: Dual Embeddings for Portability
        sa.Column("embedding_secondary", Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=False, server_default="all-MiniLM-L6-v2"),
        sa.Column("source_type", sa.String(50), nullable=False, server_default="explicit"),
        # B01: Ebbinghaus Decay Engine columns
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("decay_rate", sa.Float(), nullable=False, server_default="0.005"),
        # B02: Memory category for domain-specific decay rates
        sa.Column("memory_category", sa.String(100), nullable=True, server_default="fact"),
        # C01–C03: Memory Integrity Proof columns
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("merkle_leaf", sa.String(64), nullable=True),
        sa.Column("merkle_root", sa.String(64), nullable=True),
        sa.Column("nonce", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_semantic_agent_subject", "semantic_memories", ["agent_id", "subject"])
    op.create_index("ix_semantic_agent_spo", "semantic_memories", ["agent_id", "subject", "predicate"])
    op.create_index("ix_semantic_tenant", "semantic_memories", ["tenant_id"])

    op.execute("""
        CREATE INDEX ix_semantic_not_deleted
        ON semantic_memories (agent_id)
        WHERE deleted_at IS NULL
    """)

    op.execute("""
        CREATE INDEX ix_semantic_embedding_hnsw
        ON semantic_memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)


def downgrade() -> None:
    # Drop indexes first, then table
    op.execute("DROP INDEX IF EXISTS ix_semantic_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_semantic_not_deleted")
    op.drop_index("ix_semantic_tenant", "semantic_memories")
    op.drop_index("ix_semantic_agent_spo", "semantic_memories")
    op.drop_index("ix_semantic_agent_subject", "semantic_memories")
    op.drop_table("semantic_memories")
