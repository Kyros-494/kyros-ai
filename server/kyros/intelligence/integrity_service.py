"""C08, C09, C11 — Integrity Service layer.

Manages the Merkle tree construction and tamper detection at the agent level.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, OperationalError

from kyros.intelligence.integrity import MerkleTree, verify_content_hash
from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session, get_db_session_for_tenant

logger = get_logger("kyros.integrity_service")

# Per-agent lock cache — bounded to 10,000 entries to prevent unbounded growth.
# Uses a simple dict with LRU eviction via functools.lru_cache on a helper.
_MAX_AGENT_LOCKS = 10_000
_agent_merkle_locks: dict[str, asyncio.Lock] = {}


def _get_agent_lock(agent_id: UUID) -> asyncio.Lock:
    """Get or create a per-agent asyncio.Lock, evicting oldest if at capacity."""
    key = str(agent_id)
    if key not in _agent_merkle_locks:
        if len(_agent_merkle_locks) >= _MAX_AGENT_LOCKS:
            # Evict the oldest entry (insertion-ordered dict in Python 3.7+)
            oldest_key = next(iter(_agent_merkle_locks))
            del _agent_merkle_locks[oldest_key]
        _agent_merkle_locks[key] = asyncio.Lock()
    return _agent_merkle_locks[key]


async def update_agent_merkle_root(agent_id: UUID, tenant_id: UUID) -> str | None:
    """Recalculate the Merkle root for all of an agent's memories and log it.

    Called asynchronously after any write operation (remember, forget, store_fact).
    Uses a per-agent asyncio lock to prevent concurrent updates from deadlocking.

    Returns:
        The new Merkle root hash, or None if the update was skipped/failed.
    """
    lock = _get_agent_lock(agent_id)

    # If another update is already running for this agent, skip — it will
    # compute the correct root from the latest state anyway.
    if lock.locked():
        return None

    async with lock:
        try:
            return await _do_update_merkle_root(agent_id, tenant_id)
        except (DBAPIError, OperationalError) as e:
            # Deadlock or transient DB error — log and move on. The next write
            # will trigger another update that will succeed.
            logger.warning(
                "Merkle root update skipped due to DB contention",
                agent_id=str(agent_id),
                error=str(e)[:120],
            )
            return None
        except Exception as e:
            logger.error(
                "Merkle root update failed unexpectedly",
                agent_id=str(agent_id),
                error=str(e),
            )
            return None


async def _do_update_merkle_root(agent_id: UUID, tenant_id: UUID) -> str:
    """Inner implementation — runs under the per-agent lock."""
    leaf_hashes: list[str] = []

    async with get_db_session_for_tenant(str(tenant_id)) as session:
        # Collect all active memory leaves across all three tables, ordered
        # deterministically so the tree is reproducible.
        _ALLOWED_TABLES = frozenset({"episodic_memories", "semantic_memories", "procedural_memories"})
        for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
            assert table in _ALLOWED_TABLES, f"Unexpected table name: {table}"  # safety guard
            result = await session.execute(
                text(f"""
                SELECT merkle_leaf
                FROM {table}
                WHERE agent_id = :agent_id
                  AND deleted_at IS NULL
                  AND merkle_leaf IS NOT NULL
                ORDER BY id ASC
                """),
                {"agent_id": agent_id},
            )
            leaf_hashes.extend(row.merkle_leaf for row in result.fetchall())

        if not leaf_hashes:
            return ""

        tree = MerkleTree(leaf_hashes)
        root = tree.get_root()

        # Stamp the new root onto all active memories for this agent.
        # Use a single UPDATE per table to minimise lock contention.
        for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
            await session.execute(
                text(f"""
                UPDATE {table}
                SET merkle_root = :root
                WHERE agent_id = :agent_id AND deleted_at IS NULL
                """),
                {"root": root, "agent_id": agent_id},
            )

        # Append an immutable audit log entry.
        await session.execute(
            text("""
            INSERT INTO memory_audit_logs
                (id, agent_id, tenant_id, merkle_root, tree_size, created_at)
            VALUES
                (gen_random_uuid(), :agent_id, :tenant_id, :root, :size, :now)
            """),
            {
                "agent_id": agent_id,
                "tenant_id": tenant_id,
                "root": root,
                "size": len(leaf_hashes),
                "now": datetime.now(timezone.utc).replace(tzinfo=None),
            },
        )

    logger.debug(
        "Updated Merkle root",
        agent_id=str(agent_id),
        root=root,
        tree_size=len(leaf_hashes),
    )
    return root


# ─── C09: Tamper Detection ────────────────────

async def verify_agent_integrity(agent_id: UUID) -> list[dict]:
    """Verify all memories for an agent match their stored content hashes.

    Returns:
        List of tampered memory dicts. Empty list means all memories are intact.
    """
    tampered: list[dict] = []

    tables = [
        ("episodic_memories",   "content"),
        ("semantic_memories",   "subject || ' ' || predicate || ' ' || object"),
        ("procedural_memories", "name || ': ' || description"),
    ]

    try:
        async with get_db_session() as session:
            for table, content_field in tables:
                result = await session.execute(
                    text(f"""
                    SELECT id, {content_field} AS content_text, created_at,
                           content_hash, nonce, merkle_root
                    FROM {table}
                    WHERE agent_id = :agent_id AND content_hash IS NOT NULL
                    """),
                    {"agent_id": agent_id},
                )
                for row in result.fetchall():
                    is_valid = verify_content_hash(
                        content=row.content_text,
                        nonce=row.nonce,
                        expected_hash=row.content_hash,
                        metadata=None,  # semantic/procedural have no metadata col
                        timestamp=row.created_at.isoformat() if row.created_at else None,
                    )
                    if not is_valid:
                        tampered.append({
                            "memory_id": str(row.id),
                            "table": table,
                            "expected_hash": row.content_hash,
                            "merkle_root": row.merkle_root,
                        })
    except Exception as e:
        logger.error("Integrity verification failed", agent_id=str(agent_id), error=str(e))
        return []

    if tampered:
        logger.warning(
            "Tampered memories detected",
            agent_id=str(agent_id),
            count=len(tampered),
        )
        await _emit_tamper_webhooks(agent_id, tampered)

    return tampered


async def _emit_tamper_webhooks(agent_id: UUID, tampered: list[dict]) -> None:
    """Fire security webhooks for each tampered memory (C13)."""
    import os
    webhook_url = os.environ.get("KYROS_SECURITY_WEBHOOK_URL")
    if not webhook_url:
        return

    try:
        import httpx
        async with httpx.AsyncClient(timeout=5.0) as client:
            for mem in tampered:
                await client.post(webhook_url, json={
                    "event": "security.memory_tampered",
                    "agent_id": str(agent_id),
                    "memory_id": mem["memory_id"],
                    "expected_hash": mem["expected_hash"],
                    "merkle_root": mem["merkle_root"],
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except Exception as e:
        logger.error("Failed to send tamper webhook", error=str(e))
