"""E15 — Create tenants and agents tables

Revision ID: 0001
Revises: None
Create Date: 2026-04-25
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ── Tenants ─────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("api_key_hash", sa.String(255), nullable=False, unique=True),
        sa.Column("plan", sa.String(50), nullable=False, server_default="free"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
    )

    # Performance indexes for tenants
    op.create_index("ix_tenants_email", "tenants", ["email"], unique=True)
    op.create_index("ix_tenants_api_key_hash", "tenants", ["api_key_hash"], unique=True)
    op.create_index("ix_tenants_is_active", "tenants", ["is_active"])

    # ── Agents ──────────────────────────────────
    op.create_table(
        "agents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(255), nullable=True),
        sa.Column("metadata", JSONB, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("tenant_id", "external_id", name="uq_agent_tenant_external"),
    )

    # Performance indexes for agents
    op.create_index("ix_agents_tenant_id", "agents", ["tenant_id"])
    op.create_index(
        "ix_agents_tenant_external", "agents", ["tenant_id", "external_id"], unique=True
    )
    op.create_index("ix_agents_created_at", "agents", ["created_at"])


def downgrade() -> None:
    # Drop indexes first, then tables (reverse order of creation)
    op.drop_index("ix_agents_created_at", "agents")
    op.drop_index("ix_agents_tenant_external", "agents")
    op.drop_index("ix_agents_tenant_id", "agents")
    op.drop_table("agents")

    op.drop_index("ix_tenants_is_active", "tenants")
    op.drop_index("ix_tenants_api_key_hash", "tenants")
    op.drop_index("ix_tenants_email", "tenants")
    op.drop_table("tenants")
