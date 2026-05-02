"""E11 — Alembic migration: Semantic Propagation Logs table.

Adds the semantic_propagation_logs table for auditing belief propagation updates.

Revision ID: e11_propagation_logs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "semantic_propagation_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("fact_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("semantic_memories.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by_fact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("old_confidence", sa.Float(), nullable=False),
        sa.Column("new_confidence", sa.Float(), nullable=False),
        sa.Column("depth", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_sem_prop_log_agent", "semantic_propagation_logs", ["agent_id"])
    op.create_index("ix_sem_prop_log_fact", "semantic_propagation_logs", ["fact_id"])


def downgrade() -> None:
    op.drop_index("ix_sem_prop_log_fact", table_name="semantic_propagation_logs")
    op.drop_index("ix_sem_prop_log_agent", table_name="semantic_propagation_logs")
    op.drop_table("semantic_propagation_logs")
