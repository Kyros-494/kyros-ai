"""Compression scheduler — finds agents with >100 uncompressed memories
and runs the L1→L2→L3 compression pipeline.

Usage:
    python -m kyros.intelligence.scheduler          # one-shot run
    0 */6 * * * python -m kyros.intelligence.scheduler  # cron every 6h
"""

from __future__ import annotations

import asyncio
import json
import time
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.intelligence.compression import CompressionEngine, MIN_MEMORIES_TO_COMPRESS, HistoryCard
from kyros.storage.postgres import get_db_session, get_db_session_for_tenant
from kyros.logging import get_logger

logger = get_logger("kyros.intelligence.scheduler")

# Process agents in pages to avoid loading millions of rows at once
_PAGE_SIZE = 100


async def find_agents_needing_compression(offset: int = 0) -> list[dict]:
    """Find one page of agents with enough uncompressed memories."""
    async with get_db_session() as session:
        result = await session.execute(
            text("""
            SELECT a.id AS agent_id, a.external_id, a.tenant_id,
                   COUNT(e.id) AS uncompressed_count
            FROM agents a
            JOIN episodic_memories e ON e.agent_id = a.id
            WHERE e.compression_level = 0
              AND e.deleted_at IS NULL
            GROUP BY a.id, a.external_id, a.tenant_id
            HAVING COUNT(e.id) >= :min_count
            ORDER BY uncompressed_count DESC
            LIMIT :limit OFFSET :offset
            """),
            {"min_count": MIN_MEMORIES_TO_COMPRESS, "limit": _PAGE_SIZE, "offset": offset},
        )
        return [
            {
                "agent_id": row.agent_id,
                "external_id": row.external_id,
                "tenant_id": row.tenant_id,
                "uncompressed_count": row.uncompressed_count,
            }
            for row in result.fetchall()
        ]


async def compress_agent(
    agent_id: UUID, tenant_id: UUID, engine: CompressionEngine
) -> HistoryCard | None:
    """Run the full compression pipeline for a single agent.

    Uses a tenant-scoped session (RLS) for both read and write to ensure
    correct row-level security and consistency within one transaction.
    """
    start = time.monotonic()

    async with get_db_session_for_tenant(str(tenant_id)) as session:
        # Read and lock rows for this agent in one transaction
        result = await session.execute(
            text("""
            SELECT id, content, importance, created_at
            FROM episodic_memories
            WHERE agent_id = :agent_id
              AND compression_level = 0
              AND deleted_at IS NULL
            ORDER BY created_at ASC
            FOR UPDATE SKIP LOCKED
            """),
            {"agent_id": agent_id},
        )
        rows = result.fetchall()

        if not rows:
            return None

        raw_memories = [
            {
                "id": str(row.id),
                "content": row.content,
                "importance": row.importance,
                "created_at": row.created_at.isoformat() if row.created_at else "",
            }
            for row in rows
        ]

        card = engine.compress_agent_memories(raw_memories)
        card.agent_id = str(agent_id)

        # Mark originals as compressed (within the same transaction)
        memory_ids = [row.id for row in rows]
        await session.execute(
            text("""
            UPDATE episodic_memories
            SET compression_level = 1
            WHERE id = ANY(:ids)
            """),
            {"ids": memory_ids},
        )

        # Store the L3 history card
        card_id = uuid4()
        await session.execute(
            text("""
            INSERT INTO episodic_memories
                (id, agent_id, tenant_id, content, content_type,
                 compression_level, importance, metadata, created_at)
            VALUES
                (:id, :agent_id, :tenant_id, :content, 'text',
                 3, 1.0, :metadata, NOW())
            """),
            {
                "id": card_id,
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "content": card.summary,
                "metadata": json.dumps({
                    "compression": True,
                    "level": 3,
                    "source_count": card.memory_count,
                    "compression_ratio": card.compression_ratio,
                    "levels": card.levels,
                }),
            },
        )

    elapsed = (time.monotonic() - start) * 1000
    logger.info(
        "Agent compressed",
        agent_id=str(agent_id),
        memories=len(rows),
        ratio=card.compression_ratio,
        latency_ms=round(elapsed, 2),
    )
    return card


async def run_compression_cycle() -> list[HistoryCard]:
    """Run one full compression cycle across all eligible agents (paginated)."""
    logger.info("Starting compression cycle")
    engine = CompressionEngine()
    results: list[HistoryCard] = []
    offset = 0

    while True:
        agents = await find_agents_needing_compression(offset=offset)
        if not agents:
            break

        logger.info("Processing compression page", offset=offset, count=len(agents))

        for agent in agents:
            try:
                card = await compress_agent(
                    agent_id=agent["agent_id"],
                    tenant_id=agent["tenant_id"],
                    engine=engine,
                )
                if card:
                    results.append(card)
            except Exception as e:
                logger.error(
                    "Compression failed for agent",
                    agent_id=str(agent["agent_id"]),
                    error=str(e),
                )

        if len(agents) < _PAGE_SIZE:
            break  # last page
        offset += _PAGE_SIZE

    logger.info("Compression cycle complete", agents_processed=len(results))
    return results


if __name__ == "__main__":
    asyncio.run(run_compression_cycle())
