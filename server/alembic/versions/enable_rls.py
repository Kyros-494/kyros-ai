"""E20 — Enable Row-Level Security (RLS) on all memory tables

Revision ID: 0006
Revises: 0005
Create Date: 2026-04-25

RLS ensures that even if application-level bugs occur, one tenant's data
can never leak to another tenant.

IMPORTANT: The app sets the tenant context before every query via:
    SET LOCAL kyros.current_tenant_id = '<uuid>';

This is handled automatically by the auth middleware. The RLS policy
uses current_setting() with missing_ok=true so queries without the
setting return no rows (fail-safe default-deny) rather than raising.

SECURITY NOTE: The database password for kyros_app role must be set via
environment variable KYROS_DB_APP_PASSWORD before running this migration.
Never hardcode passwords in migration files.
"""

import os
from collections.abc import Sequence

from sqlalchemy import text

from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tables that hold tenant-scoped data
RLS_TABLES = [
    "agents",
    "episodic_memories",
    "semantic_memories",
    "procedural_memories",
    "usage_events",
]


def upgrade() -> None:
    """Enable RLS on all tenant-scoped tables and create app role."""
    for table in RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        # current_setting(..., true) returns NULL (not an error) when the GUC
        # is not set — USING clause evaluates to NULL → no rows returned (safe).
        op.execute(
            f"CREATE POLICY tenant_isolation_policy ON {table} "
            "USING ("
            "  tenant_id = NULLIF("
            "    current_setting('kyros.current_tenant_id', true), ''"
            "  )::uuid"
            ")"
        )

    # Create a dedicated app role that respects RLS.
    # Password must be provided via environment variable for security.
    # In test/CI environments, use a default test password if not set.
    app_password = os.environ.get("KYROS_DB_APP_PASSWORD")
    is_test_env = os.environ.get("KYROS_ENVIRONMENT") in ("test", "ci", "development")

    if not app_password:
        if is_test_env:
            app_password = "test-password-change-in-production"
        else:
            raise ValueError(
                "KYROS_DB_APP_PASSWORD environment variable must be set before running this migration. "
                "Generate a strong password with: openssl rand -base64 32"
            )

    # Use parameterized query to safely pass password
    connection = op.get_bind()
    connection.execute(
        text(
            "DO $$ "
            "BEGIN "
            "  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'kyros_app') THEN "
            "    EXECUTE format('CREATE ROLE kyros_app LOGIN PASSWORD %L', :password); "
            "  END IF; "
            "END $$"
        ),
        {"password": app_password},
    )

    for table in RLS_TABLES:
        op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO kyros_app")

    # tenants has no RLS — it IS the identity table
    op.execute("GRANT SELECT, INSERT, UPDATE ON tenants TO kyros_app")


def downgrade() -> None:
    """Disable RLS and revoke permissions."""
    for table in reversed(RLS_TABLES):
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    for table in [*RLS_TABLES, "tenants"]:
        op.execute(f"REVOKE ALL ON {table} FROM kyros_app")
