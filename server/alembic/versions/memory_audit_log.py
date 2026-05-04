"""C07 — Alembic migration: Memory Audit Log table.

Adds the memory_audit_logs table for appending Merkle roots
and tree sizes for immutable cryptographic integrity tracking.

Revision ID: c07_memory_audit_log
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
        "memory_audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("agents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),
        sa.Column("merkle_root", sa.String(length=64), nullable=False),
        sa.Column("tree_size", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_agent_created", "memory_audit_logs", ["agent_id", "created_at"])
    op.create_index("ix_audit_tenant", "memory_audit_logs", ["tenant_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_tenant", table_name="memory_audit_logs")
    op.drop_index("ix_audit_agent_created", table_name="memory_audit_logs")
    op.drop_table("memory_audit_logs")
