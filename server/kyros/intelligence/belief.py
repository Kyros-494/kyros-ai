"""E02–E06 — Belief Propagation Network.

Maintains a graph of semantic facts connected by semantic relatedness.
When a fact's confidence changes, the delta propagates to related facts
to keep the agent's worldview consistent.
"""

from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.belief")

# Maximum BFS queue size — prevents unbounded memory growth on dense graphs
_MAX_QUEUE_SIZE = 10_000


# ─── E02 & E03: Fact Relationship Indexer ─────


async def index_fact_relationships(
    tenant_id: UUID | None,
    agent_id: UUID,
    fact_id: UUID,
    embedding: list[float],
    threshold: float = 0.75,
) -> None:
    """Compute and store cosine-similarity edges to existing facts.

    Called asynchronously after a new fact is stored in semantic_memories.

    Args:
        tenant_id: The tenant ID.
        agent_id: The agent ID.
        fact_id: The ID of the newly inserted fact.
        embedding: The vector embedding of the new fact.
        threshold: Minimum cosine similarity to create an edge (default 0.75).
    """
    if tenant_id is None:
        raise ValueError("tenant_id is required for belief indexing")

    from kyros.storage.postgres import get_db_session_for_tenant

    async with get_db_session_for_tenant(str(tenant_id)) as session:
        result = await session.execute(
            text("""
            SELECT id, 1 - (embedding <=> :embedding) AS sim
            FROM semantic_memories
            WHERE agent_id = :agent_id
              AND deleted_at IS NULL
              AND id != :fact_id
              AND 1 - (embedding <=> :embedding) >= :threshold
            """),
            {
                "agent_id": agent_id,
                "fact_id": fact_id,
                "embedding": embedding,
                "threshold": threshold,
            },
        )
        related_facts = result.fetchall()

        if not related_facts:
            return

        now = datetime.now(UTC).replace(tzinfo=None)

        # Batch-insert all edges in a single executemany call
        edge_rows = []
        for row in related_facts:
            sim = float(row.sim)
            # Both directions (undirected graph)
            edge_rows.append(
                {
                    "id": uuid4(),
                    "agent_id": agent_id,
                    "tenant_id": tenant_id,
                    "from_id": fact_id,
                    "to_id": row.id,
                    "sim": sim,
                    "now": now,
                }
            )
            edge_rows.append(
                {
                    "id": uuid4(),
                    "agent_id": agent_id,
                    "tenant_id": tenant_id,
                    "from_id": row.id,
                    "to_id": fact_id,
                    "sim": sim,
                    "now": now,
                }
            )

        await session.execute(
            text("""
            INSERT INTO semantic_edges
                (id, agent_id, tenant_id, from_fact_id, to_fact_id, relatedness_score, created_at)
            VALUES
                (:id, :agent_id, :tenant_id, :from_id, :to_id, :sim, :now)
            ON CONFLICT (from_fact_id, to_fact_id) DO NOTHING
            """),
            edge_rows,
        )

    logger.debug(
        "Indexed fact relationships",
        agent_id=str(agent_id),
        fact_id=str(fact_id),
        edges_created=len(related_facts) * 2,
    )


# ─── E06 & E08: Loopy Belief Propagation ──────


async def run_belief_propagation(
    agent_id: UUID,
    start_fact_id: UUID,
    delta_confidence: float,
    max_depth: int = 3,
    min_confidence: float = 0.05,
) -> list[dict]:
    """Propagate confidence changes through the semantic belief graph.

    Uses BFS with batched neighbor fetching to avoid N+1 queries.
    Bounded by max_depth and _MAX_QUEUE_SIZE to prevent runaway propagation.

    Args:
        agent_id: The agent ID.
        start_fact_id: The fact whose confidence was externally changed.
        delta_confidence: The change in confidence (e.g., -0.2).
        max_depth: Maximum hops to traverse (default 3).
        min_confidence: Confidence floor — never drops below this (default 0.05).

    Returns:
        List of dicts describing which facts were updated and by how much.
    """
    if abs(delta_confidence) < 0.01:
        return []

    updates: list[dict] = []
    db_updates: list[dict] = []
    log_inserts: list[dict] = []
    now = datetime.now(UTC).replace(tzinfo=None)

    # BFS queue: (fact_id, propagated_delta, depth)
    queue: deque[tuple[UUID, float, int]] = deque()
    queue.append((start_fact_id, delta_confidence, 0))
    visited: set[UUID] = {start_fact_id}

    # Belief propagation reads/writes facts — use non-tenant session since
    # agent_id is always scoped in the WHERE clause and this is called
    # from within an already-authenticated request context.
    async with get_db_session() as session:
        while queue:
            if len(queue) > _MAX_QUEUE_SIZE:
                logger.warning(
                    "Belief propagation queue limit reached — truncating",
                    agent_id=str(agent_id),
                    queue_size=len(queue),
                )
                break

            current_id, current_delta, depth = queue.popleft()

            if depth >= max_depth:
                continue

            # Batch-fetch ALL neighbors of current node in one query
            result = await session.execute(
                text("""
                SELECT to_fact_id, relatedness_score
                FROM semantic_edges
                WHERE from_fact_id = :from_id AND agent_id = :agent_id
                """),
                {"from_id": current_id, "agent_id": agent_id},
            )
            neighbors = result.fetchall()

            if not neighbors:
                continue

            # Batch-fetch confidence for all unvisited neighbors in one query
            unvisited_ids = [n.to_fact_id for n in neighbors if n.to_fact_id not in visited]
            if not unvisited_ids:
                continue

            conf_result = await session.execute(
                text("""
                SELECT id, confidence, subject, predicate, object
                FROM semantic_memories
                WHERE id = ANY(:ids) AND deleted_at IS NULL
                """),
                {"ids": unvisited_ids},
            )
            conf_map = {row.id: row for row in conf_result.fetchall()}

            for neighbor in neighbors:
                neighbor_id = neighbor.to_fact_id
                if neighbor_id in visited or neighbor_id not in conf_map:
                    continue

                relatedness = float(neighbor.relatedness_score)
                neighbor_delta = current_delta * relatedness * 0.5  # decay factor

                if abs(neighbor_delta) < 0.01:
                    continue

                row = conf_map[neighbor_id]
                old_conf = float(row.confidence)
                new_conf = max(min_confidence, min(1.0, old_conf + neighbor_delta))
                actual_delta = new_conf - old_conf

                if abs(actual_delta) <= 0.001:
                    continue

                db_updates.append({"b_id": neighbor_id, "b_conf": new_conf, "b_now": now})
                log_inserts.append(
                    {
                        "id": uuid4(),
                        "agent_id": agent_id,
                        "fact_id": neighbor_id,
                        "triggered_by_fact_id": current_id,
                        "old_confidence": old_conf,
                        "new_confidence": new_conf,
                        "depth": depth + 1,
                        "created_at": now,
                    }
                )
                updates.append(
                    {
                        "fact_id": str(neighbor_id),
                        "statement": f"{row.subject} {row.predicate} {row.object}",
                        "old_confidence": round(old_conf, 4),
                        "new_confidence": round(new_conf, 4),
                        "delta": round(actual_delta, 4),
                        "depth": depth + 1,
                        "triggered_by": str(current_id),
                    }
                )

                visited.add(neighbor_id)
                queue.append((neighbor_id, actual_delta, depth + 1))

        # Bulk-write all updates in two executemany calls
        if db_updates:
            await session.execute(
                text("""
                UPDATE semantic_memories
                SET confidence = :b_conf, updated_at = :b_now
                WHERE id = :b_id
                """),
                db_updates,
            )

        if log_inserts:
            await session.execute(
                text("""
                INSERT INTO semantic_propagation_logs
                    (id, agent_id, fact_id, triggered_by_fact_id,
                     old_confidence, new_confidence, depth, created_at)
                VALUES
                    (:id, :agent_id, :fact_id, :triggered_by_fact_id,
                     :old_confidence, :new_confidence, :depth, :created_at)
                """),
                log_inserts,
            )

    if updates:
        logger.info(
            "Belief propagation complete",
            agent_id=str(agent_id),
            start_fact=str(start_fact_id),
            facts_updated=len(updates),
        )

    return updates
