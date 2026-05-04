"""E19 — Create usage_events table for billing metering

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Create usage_events table for billing and metering."""
    op.create_table(
        "usage_events",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("agent_id", UUID(as_uuid=True), nullable=True),
        sa.Column("operation", sa.String(100), nullable=False),
        sa.Column("memory_type", sa.String(50), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Performance indexes for billing queries
    op.create_index("ix_usage_tenant_created", "usage_events", ["tenant_id", "created_at"])
    op.create_index("ix_usage_tenant_op", "usage_events", ["tenant_id", "operation"])

    # Partition-ready: this table will be the highest write volume.
    # When needed, convert to range-partitioned by created_at (monthly).
    op.execute(
        "COMMENT ON TABLE usage_events IS 'High-write billing table. Partition by created_at when >10M rows.'"
    )


def downgrade() -> None:
    """Drop usage_events table and indexes."""
    op.drop_index("ix_usage_tenant_op", table_name="usage_events")
    op.drop_index("ix_usage_tenant_created", table_name="usage_events")
    op.drop_table("usage_events")
