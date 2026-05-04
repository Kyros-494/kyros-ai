"""D02 — Alembic migration: Causal Edges table.

Adds the causal_edges table for building the Causal Memory Graph.
Tracks why things happened (from_memory_id -> to_memory_id).

Revision ID: d02_causal_edges
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "causal_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("to_memory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation", sa.String(length=100), nullable=False, server_default="causes"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("from_memory_id", "to_memory_id", "relation", name="uq_causal_edge")
    )
    op.create_index("ix_causal_agent", "causal_edges", ["agent_id"])
    op.create_index("ix_causal_from", "causal_edges", ["from_memory_id"])
    op.create_index("ix_causal_to", "causal_edges", ["to_memory_id"])


def downgrade() -> None:
    op.drop_index("ix_causal_to", table_name="causal_edges")
    op.drop_index("ix_causal_from", table_name="causal_edges")
    op.drop_index("ix_causal_agent", table_name="causal_edges")
    op.drop_table("causal_edges")
