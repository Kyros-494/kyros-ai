"""Integration tests for Causal Memory Chains.

Tests the full causal engine:
1. Storing explicit causes
2. Graph traversal (explain)
3. Upstream and downstream traversal
4. Empty graph handling
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import text

from kyros.intelligence.causal import store_causal_edges, traverse_causal_chain


class TestCausalGraph:

    @pytest.mark.asyncio
    async def test_explicit_causal_chain_upstream_traversal(self, db_session):
        """Traversing upstream from C should find B and A as causes."""
        tenant_id = uuid4()
        agent_id = uuid4()
        mem_a_id = uuid4()
        mem_b_id = uuid4()
        mem_c_id = uuid4()

        # Seed tenant and agent
        await db_session.execute(
            text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
            {"id": tenant_id, "n": "test", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
        )
        await db_session.execute(
            text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
            {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
        )

        # Insert 3 episodic memories with minimal required fields
        for mid, content in [
            (mem_a_id, "User clicked unsubscribe"),
            (mem_b_id, "System sent exit survey"),
            (mem_c_id, "User replied with angry feedback"),
        ]:
            await db_session.execute(
                text("""
                INSERT INTO episodic_memories
                    (id, agent_id, tenant_id, content, embedding, created_at)
                VALUES (:id, :aid, :tid, :content, :emb, NOW())
                ON CONFLICT DO NOTHING
                """),
                {"id": mid, "aid": agent_id, "tid": tenant_id, "content": content, "emb": [0.1] * 384},
            )

        # Store causal edges: A → B → C
        edges = [
            {"from_memory_id": str(mem_a_id), "to_memory_id": str(mem_b_id), "relation": "causes", "description": "Click triggers survey"},
            {"from_memory_id": str(mem_b_id), "to_memory_id": str(mem_c_id), "relation": "causes", "description": "Survey prompts reply"},
        ]
        stored = await store_causal_edges(tenant_id, agent_id, edges)
        assert len(stored) == 2, f"Expected 2 stored edges, got {len(stored)}"

        # Traverse upstream from C — should find B and A
        graph = await traverse_causal_chain(agent_id, mem_c_id, max_depth=3, direction="causes")

        assert "nodes" in graph
        assert "edges" in graph
        assert len(graph["edges"]) == 2, f"Expected 2 upstream edges, got {len(graph['edges'])}"

        from_ids = {e["from"] for e in graph["edges"]}
        assert str(mem_b_id) in from_ids
        assert str(mem_a_id) in from_ids

    @pytest.mark.asyncio
    async def test_explicit_causal_chain_downstream_traversal(self, db_session):
        """Traversing downstream from A should find B and C as effects."""
        tenant_id = uuid4()
        agent_id = uuid4()
        mem_a_id = uuid4()
        mem_b_id = uuid4()
        mem_c_id = uuid4()

        await db_session.execute(
            text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
            {"id": tenant_id, "n": "test2", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
        )
        await db_session.execute(
            text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
            {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
        )

        for mid, content in [
            (mem_a_id, "Root cause event"),
            (mem_b_id, "Intermediate effect"),
            (mem_c_id, "Final outcome"),
        ]:
            await db_session.execute(
                text("""
                INSERT INTO episodic_memories
                    (id, agent_id, tenant_id, content, embedding, created_at)
                VALUES (:id, :aid, :tid, :content, :emb, NOW())
                ON CONFLICT DO NOTHING
                """),
                {"id": mid, "aid": agent_id, "tid": tenant_id, "content": content, "emb": [0.2] * 384},
            )

        edges = [
            {"from_memory_id": str(mem_a_id), "to_memory_id": str(mem_b_id), "relation": "causes", "description": "A causes B"},
            {"from_memory_id": str(mem_b_id), "to_memory_id": str(mem_c_id), "relation": "causes", "description": "B causes C"},
        ]
        await store_causal_edges(tenant_id, agent_id, edges)

        graph = await traverse_causal_chain(agent_id, mem_a_id, max_depth=3, direction="effects")

        assert len(graph["edges"]) == 2
        to_ids = {e["to"] for e in graph["edges"]}
        assert str(mem_b_id) in to_ids
        assert str(mem_c_id) in to_ids

    @pytest.mark.asyncio
    async def test_traverse_nonexistent_memory_returns_empty(self, db_session):
        """Traversing a memory that doesn't exist should return empty graph, not crash."""
        agent_id = uuid4()
        fake_memory_id = uuid4()

        graph = await traverse_causal_chain(agent_id, fake_memory_id, max_depth=3, direction="both")

        assert graph == {"nodes": [], "edges": []}

    @pytest.mark.asyncio
    async def test_store_duplicate_edges_are_idempotent(self, db_session):
        """Storing the same edge twice should not raise an error (ON CONFLICT DO NOTHING)."""
        tenant_id = uuid4()
        agent_id = uuid4()
        mem_a_id = uuid4()
        mem_b_id = uuid4()

        await db_session.execute(
            text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
            {"id": tenant_id, "n": "test3", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
        )
        await db_session.execute(
            text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
            {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
        )
        for mid, content in [(mem_a_id, "Event A"), (mem_b_id, "Event B")]:
            await db_session.execute(
                text("INSERT INTO episodic_memories (id, agent_id, tenant_id, content, embedding, created_at) VALUES (:id, :aid, :tid, :c, :emb, NOW()) ON CONFLICT DO NOTHING"),
                {"id": mid, "aid": agent_id, "tid": tenant_id, "c": content, "emb": [0.3] * 384},
            )

        edge = [{"from_memory_id": str(mem_a_id), "to_memory_id": str(mem_b_id), "relation": "causes", "description": "test"}]

        # Store twice — should not raise
        await store_causal_edges(tenant_id, agent_id, edge)
        await store_causal_edges(tenant_id, agent_id, edge)

    @pytest.mark.asyncio
    async def test_max_depth_limits_traversal(self, db_session):
        """max_depth=1 should only return direct neighbors, not transitive ones."""
        tenant_id = uuid4()
        agent_id = uuid4()
        mem_a_id = uuid4()
        mem_b_id = uuid4()
        mem_c_id = uuid4()

        await db_session.execute(
            text("INSERT INTO tenants (id, name, email, api_key_hash, created_at) VALUES (:id, :n, :e, :h, NOW()) ON CONFLICT DO NOTHING"),
            {"id": tenant_id, "n": "test4", "e": f"{tenant_id.hex[:8]}@t.com", "h": tenant_id.hex},
        )
        await db_session.execute(
            text("INSERT INTO agents (id, tenant_id, external_id, created_at) VALUES (:id, :tid, :eid, NOW()) ON CONFLICT DO NOTHING"),
            {"id": agent_id, "tid": tenant_id, "eid": f"agent-{agent_id.hex[:8]}"},
        )
        for mid, content in [(mem_a_id, "A"), (mem_b_id, "B"), (mem_c_id, "C")]:
            await db_session.execute(
                text("INSERT INTO episodic_memories (id, agent_id, tenant_id, content, embedding, created_at) VALUES (:id, :aid, :tid, :c, :emb, NOW()) ON CONFLICT DO NOTHING"),
                {"id": mid, "aid": agent_id, "tid": tenant_id, "c": content, "emb": [0.4] * 384},
            )

        edges = [
            {"from_memory_id": str(mem_a_id), "to_memory_id": str(mem_b_id), "relation": "causes", "description": "A→B"},
            {"from_memory_id": str(mem_b_id), "to_memory_id": str(mem_c_id), "relation": "causes", "description": "B→C"},
        ]
        await store_causal_edges(tenant_id, agent_id, edges)

        # With max_depth=1, traversing downstream from A should only find A→B, not A→B→C
        graph = await traverse_causal_chain(agent_id, mem_a_id, max_depth=1, direction="effects")
        assert len(graph["edges"]) == 1
        assert graph["edges"][0]["to"] == str(mem_b_id)
