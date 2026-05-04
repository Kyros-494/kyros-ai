"""Forgetting scheduler — soft-deletes low-value memories past their retention window.

Retention policies by plan:
    free       → 30 days
    pro        → 90 days
    team       → 365 days
    enterprise → never auto-forget
"""

from __future__ import annotations

import asyncio
import time
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import text

from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.intelligence.forgetting")

RETENTION_DAYS: dict[str, int | None] = {
    "free": 30,
    "pro": 90,
    "team": 365,
    "enterprise": None,
}

IMPORTANCE_THRESHOLD = 0.2
MIN_MEMORIES_PER_AGENT = 50


async def get_tenants_with_policies() -> list[dict]:
    """Fetch all active tenants with their plan info."""
    async with get_db_session() as session:
        result = await session.execute(text("SELECT id, plan FROM tenants WHERE is_active = true"))
        return [{"tenant_id": row.id, "plan": row.plan} for row in result.fetchall()]


async def find_forgettable_memories(tenant_id: UUID, retention_days: int) -> list[dict]:
    """Find memories eligible for forgetting.

    Uses a single aggregated query to avoid N+1 per-agent COUNT queries.
    """
    cutoff = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=retention_days)

    async with get_db_session() as session:
        # Single query: get agents with their memory counts and forgettable candidates
        # Uses a CTE to count per-agent totals and filter in one round-trip
        result = await session.execute(
            text("""
            WITH agent_counts AS (
                SELECT agent_id, COUNT(*) AS total
                FROM episodic_memories
                WHERE tenant_id = :tid AND deleted_at IS NULL
                GROUP BY agent_id
                HAVING COUNT(*) > :min_keep
            )
            SELECT e.id, e.agent_id, e.content, e.importance, e.created_at
            FROM episodic_memories e
            JOIN agent_counts ac ON ac.agent_id = e.agent_id
            WHERE e.tenant_id = :tid
              AND e.deleted_at IS NULL
              AND e.created_at < :cutoff
              AND e.importance < :threshold
              AND e.compression_level = 0
            ORDER BY e.agent_id, e.importance ASC, e.created_at ASC
            """),
            {
                "tid": tenant_id,
                "min_keep": MIN_MEMORIES_PER_AGENT,
                "cutoff": cutoff,
                "threshold": IMPORTANCE_THRESHOLD,
            },
        )
        return [
            {
                "memory_id": row.id,
                "agent_id": row.agent_id,
                "content": row.content,
                "importance": row.importance,
                "created_at": row.created_at,
            }
            for row in result.fetchall()
        ]


async def soft_delete_memories(memory_ids: list[UUID]) -> int:
    """Soft-delete a batch of memories in a single UPDATE."""
    if not memory_ids:
        return 0

    async with get_db_session() as session:
        await session.execute(
            text("""
            UPDATE episodic_memories
            SET deleted_at = NOW()
            WHERE id = ANY(:ids) AND deleted_at IS NULL
            """),
            {"ids": memory_ids},
        )
    return len(memory_ids)


async def run_forgetting_cycle() -> int:
    """Run one full forgetting cycle across all tenants."""
    start = time.monotonic()
    logger.info("Starting forgetting cycle")

    tenants = await get_tenants_with_policies()
    total_forgotten = 0

    for tenant in tenants:
        plan = tenant["plan"]
        retention = RETENTION_DAYS.get(plan)

        if retention is None:
            continue  # enterprise — never auto-forget

        try:
            forgettable = await find_forgettable_memories(
                tenant_id=tenant["tenant_id"],
                retention_days=retention,
            )
            if forgettable:
                memory_ids = [m["memory_id"] for m in forgettable]
                count = await soft_delete_memories(memory_ids)
                total_forgotten += count
                logger.info(
                    "Forgotten memories",
                    tenant_id=str(tenant["tenant_id"]),
                    plan=plan,
                    count=count,
                )
        except Exception as e:
            logger.error(
                "Forgetting failed for tenant",
                tenant_id=str(tenant["tenant_id"]),
                error=str(e),
            )

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        "Forgetting cycle complete",
        total_forgotten=total_forgotten,
        tenants_processed=len(tenants),
        latency_ms=round(elapsed, 2),
    )
    return total_forgotten


if __name__ == "__main__":
    asyncio.run(run_forgetting_cycle())
