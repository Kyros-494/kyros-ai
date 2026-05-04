"""Seed test tenant and API key for integration tests."""

from __future__ import annotations

import asyncio
import hashlib
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text

from kyros.storage.postgres import get_db_session

# Test tenant and API key from conftest.py
TEST_API_KEY = "mk_test_integration_test_key_12345"
TEST_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_AGENT_ID = "test-agent"


async def seed_test_tenant() -> None:
    """Create test tenant with known API key for integration tests."""
    # Hash the API key (simple hash for test purposes)
    api_key_hash = hashlib.sha256(TEST_API_KEY.encode()).hexdigest()

    async with get_db_session() as session:
        # Insert test tenant
        await session.execute(
            text("""
            INSERT INTO tenants (
                id, name, email, api_key_hash, plan, is_active, created_at, updated_at
            )
            VALUES (:id, :name, :email, :hash, 'free', true, NOW(), NOW())
            ON CONFLICT (id) DO UPDATE SET
                api_key_hash = EXCLUDED.api_key_hash,
                updated_at = NOW()
            """),
            {
                "id": TEST_TENANT_ID,
                "name": "Test Tenant",
                "email": "test@kyros.test",
                "hash": api_key_hash,
            },
        )

        # Insert test agent
        await session.execute(
            text("""
            INSERT INTO agents (
                id, tenant_id, name, created_at, updated_at
            )
            VALUES (:id, :tenant_id, :name, NOW(), NOW())
            ON CONFLICT (id) DO NOTHING
            """),
            {
                "id": TEST_AGENT_ID,
                "tenant_id": TEST_TENANT_ID,
                "name": "Test Agent",
            },
        )

        await session.commit()

    print(f"✅ Test tenant created: {TEST_TENANT_ID}")
    print(f"✅ Test API key: {TEST_API_KEY}")
    print(f"✅ Test agent: {TEST_AGENT_ID}")


if __name__ == "__main__":
    asyncio.run(seed_test_tenant())
