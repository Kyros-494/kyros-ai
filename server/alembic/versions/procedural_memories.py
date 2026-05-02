"""E18 — Create procedural_memories table with indexes

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "procedural_memories",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("task_type", sa.String(255), nullable=False),
        sa.Column("steps", JSONB, nullable=False),
        sa.Column("embedding", Vector(384), nullable=False),
        # F01, F02: Dual Embeddings for Portability
        sa.Column("embedding_secondary", Vector(1536), nullable=True),
        sa.Column("embedding_model", sa.String(100), nullable=False, server_default="all-MiniLM-L6-v2"),
        sa.Column("success_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("avg_duration_ms", sa.Float(), nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        # B01: Ebbinghaus Decay Engine columns
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("decay_rate", sa.Float(), nullable=False, server_default="0.01"),
        # B02: Memory category for domain-specific decay rates
        sa.Column("memory_category", sa.String(100), nullable=True, server_default="workflow"),
        # C01–C03: Memory Integrity Proof columns
        sa.Column("content_hash", sa.String(64), nullable=True),
        sa.Column("merkle_leaf", sa.String(64), nullable=True),
        sa.Column("merkle_root", sa.String(64), nullable=True),
        sa.Column("nonce", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )

    op.create_index("ix_procedural_agent_task", "procedural_memories", ["agent_id", "task_type"])
    op.create_index("ix_procedural_tenant", "procedural_memories", ["tenant_id"])

    op.execute("""
        CREATE INDEX ix_procedural_not_deleted
        ON procedural_memories (agent_id)
        WHERE deleted_at IS NULL
    """)

    op.execute("""
        CREATE INDEX ix_procedural_embedding_hnsw
        ON procedural_memories
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 200)
    """)


def downgrade() -> None:
    # Drop indexes first, then table
    op.execute("DROP INDEX IF EXISTS ix_procedural_embedding_hnsw")
    op.execute("DROP INDEX IF EXISTS ix_procedural_not_deleted")
    op.drop_index("ix_procedural_tenant", "procedural_memories")
    op.drop_index("ix_procedural_agent_task", "procedural_memories")
    op.drop_table("procedural_memories")
