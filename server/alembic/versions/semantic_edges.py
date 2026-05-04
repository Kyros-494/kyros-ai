"""E05 — Alembic migration: Semantic Edges table.

Adds the semantic_edges table for the Belief Propagation Network.
Connects facts based on cosine similarity of their embeddings.

Revision ID: e05_semantic_edges
"""

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "semantic_edges",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "from_fact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("semantic_memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "to_fact_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("semantic_memories.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("relatedness_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("from_fact_id", "to_fact_id", name="uq_semantic_edge"),
    )
    op.create_index("ix_sem_edge_agent", "semantic_edges", ["agent_id"])
    op.create_index("ix_sem_edge_from", "semantic_edges", ["from_fact_id"])
    op.create_index("ix_sem_edge_to", "semantic_edges", ["to_fact_id"])


def downgrade() -> None:
    op.drop_index("ix_sem_edge_to", table_name="semantic_edges")
    op.drop_index("ix_sem_edge_from", table_name="semantic_edges")
    op.drop_index("ix_sem_edge_agent", table_name="semantic_edges")
    op.drop_table("semantic_edges")
