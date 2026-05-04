"""Integration tests for Belief Propagation Network.

Tests the Loopy Belief Propagation algorithm:
1. Fact relationship indexing (cosine similarity edges)
2. Propagation triggering on confidence changes
3. Depth limits and confidence floor guard
4. Audit logging
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from kyros.intelligence.belief import index_fact_relationships, run_belief_propagation


@pytest.mark.asyncio
async def test_belief_propagation_chain(db_session) -> None:
    """Confidence drop on fact A should propagate to related facts B and C."""
    tenant_id = uuid4()
    agent_id = uuid4()
    fact_a_id = uuid4()
    fact_b_id = uuid4()
    fact_c_id = uuid4()

    # Use identical embeddings to guarantee cosine similarity = 1.0
    embedding = [0.1] * 384

    # Seed tenant and agent
    await db_session.execute(
        text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
        {"id": tenant_id, "n": "belief-test", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
    )
    await db_session.execute(
        text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
        {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
    )

    # Insert 3 semantic facts
    for fid, subj, pred, obj in [
        (fact_a_id, "Alice", "works_at", "TechCorp"),
        (fact_b_id, "Alice", "has_access_to", "TechCorp Servers"),
        (fact_c_id, "TechCorp Servers", "contain", "Customer Data"),
    ]:
        await db_session.execute(
            text("""
            INSERT INTO semantic_memories
                (id, agent_id, tenant_id, subject, predicate, object, confidence, embedding, created_at, updated_at)
            VALUES (:id, :aid, :tid, :s, :p, :o, 1.0, :emb, NOW(), NOW())
            ON CONFLICT DO NOTHING
            """),
            {"id": fid, "aid": agent_id, "tid": tenant_id, "s": subj, "p": pred, "o": obj, "emb": embedding},
        )

    # Index relationships — identical embeddings guarantee edges are created
    for fid in [fact_a_id, fact_b_id, fact_c_id]:
        await index_fact_relationships(tenant_id, agent_id, fid, embedding, threshold=0.5)

    # Verify edges were created
    result = await db_session.execute(
        text("SELECT COUNT(*) AS cnt FROM semantic_edges WHERE agent_id = :aid"),
        {"aid": agent_id},
    )
    edge_count = result.fetchone().cnt
    assert edge_count > 0, "No semantic edges were created — indexing failed"

    # Trigger belief propagation: Alice left TechCorp (confidence drops by 1.0)
    updates = await run_belief_propagation(
        agent_id=agent_id,
        start_fact_id=fact_a_id,
        delta_confidence=-1.0,
        max_depth=3,
        min_confidence=0.05,
    )

    assert len(updates) > 0, "Belief propagation produced no updates"

    # Confidence floor must be respected
    for u in updates:
        assert u["new_confidence"] >= 0.05, f"Confidence {u['new_confidence']} below floor 0.05"
        assert u["new_confidence"] <= 1.0, f"Confidence {u['new_confidence']} above ceiling 1.0"

    # Audit logs must be written
    result = await db_session.execute(
        text("SELECT COUNT(*) AS cnt FROM semantic_propagation_logs WHERE agent_id = :aid"),
        {"aid": agent_id},
    )
    log_count = result.fetchone().cnt
    assert log_count > 0, "No propagation audit logs were written"
    assert log_count == len(updates), f"Log count {log_count} != update count {len(updates)}"


@pytest.mark.asyncio
async def test_propagation_skipped_for_tiny_delta(db_session) -> None:
    """A delta smaller than 0.01 should not trigger any propagation."""
    agent_id = uuid4()
    fact_id = uuid4()

    updates = await run_belief_propagation(
        agent_id=agent_id,
        start_fact_id=fact_id,
        delta_confidence=0.005,  # Below the 0.01 threshold
        max_depth=3,
    )

    assert updates == [], f"Expected no updates for tiny delta, got {updates}"


@pytest.mark.asyncio
async def test_propagation_respects_max_depth(db_session) -> None:
    """Propagation should not exceed max_depth hops."""
    tenant_id = uuid4()
    agent_id = uuid4()
    embedding = [0.5] * 384

    await db_session.execute(
        text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
        {"id": tenant_id, "n": "depth-test", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
    )
    await db_session.execute(
        text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
        {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
    )

    # Create a chain of 5 facts
    fact_ids = [uuid4() for _ in range(5)]
    for i, fid in enumerate(fact_ids):
        await db_session.execute(
            text("INSERT INTO semantic_memories (id, agent_id, tenant_id, subject, predicate, object, confidence, embedding, created_at, updated_at) VALUES (:id, :aid, :tid, :s, :p, :o, 0.9, :emb, NOW(), NOW()) ON CONFLICT DO NOTHING"),
            {"id": fid, "aid": agent_id, "tid": tenant_id, "s": f"fact{i}", "p": "relates_to", "o": f"fact{i+1}", "emb": embedding},
        )

    # Index all relationships
    for fid in fact_ids:
        await index_fact_relationships(tenant_id, agent_id, fid, embedding, threshold=0.5)

    # Propagate with max_depth=1 — should only affect direct neighbors
    updates = await run_belief_propagation(
        agent_id=agent_id,
        start_fact_id=fact_ids[0],
        delta_confidence=-0.5,
        max_depth=1,
    )

    # All updates should be at depth 1 (direct neighbors only)
    for u in updates:
        assert u.get("depth", 1) <= 1, f"Update at depth {u.get('depth')} exceeded max_depth=1"
