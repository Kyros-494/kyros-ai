"""D03–D06 — Causal Memory Graph Engine.

Builds and queries the 'WHY' layer of the memory system, linking
memories into a directed graph of cause-and-effect.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import text

from kyros.logging import get_logger
from kyros.ml.models import call_llm
from kyros.storage.postgres import get_db_session, get_db_session_for_tenant

logger = get_logger("kyros.causal")


# ─── D03: Causal Extraction Prompt ────────────

CAUSAL_EXTRACTION_PROMPT = """
You are an AI memory analysis engine.
Your task is to analyze a new memory and a set of recent/relevant memories,
and determine if there are any DIRECT causal relationships between them.

Types of relationships:
- "causes": Memory A directly caused Memory B to happen.
- "motivates": Memory A is the reason/motivation for the decision in Memory B.
- "prevents": Memory A stopped or prevented Memory B.

New Memory (ID: {new_id}):
{new_content}

Recent Context Memories:
{context_memories}

Extract causal relationships where the New Memory is either the CAUSE or the EFFECT.
Respond ONLY with a JSON array of objects. Do not include markdown formatting.
If no causal relationship exists, return an empty array [].

Format:
[
  {{
    "from_memory_id": "<cause_id>",
    "to_memory_id": "<effect_id>",
    "relation": "causes|motivates|prevents",
    "confidence": 0.95,
    "description": "Brief explanation of why A causes B"
  }}
]
"""


# ─── D04: Causal Extractor Service ────────────

async def extract_and_store_causal_edges(
    tenant_id: UUID | None,
    agent_id: UUID,
    new_memory_id: UUID,
    new_content: str,
    recent_memories: list[dict],
) -> list[dict]:
    """Analyze a new memory against context and extract causal edges using LLM.

    Args:
        tenant_id: The tenant ID.
        agent_id: The agent ID.
        new_memory_id: The ID of the newly stored memory.
        new_content: The content of the new memory.
        recent_memories: List of dicts with 'id' and 'content' of recent/relevant memories.

    Returns:
        List of created causal edge dictionaries.
    """
    if not recent_memories:
        return []

    # Format context
    context_str = "\n".join(
        f"- ID: {m['id']}\n  Content: {m['content']}"
        for m in recent_memories
    )

    prompt = CAUSAL_EXTRACTION_PROMPT.format(
        new_id=str(new_memory_id),
        new_content=new_content,
        context_memories=context_str,
    )

    try:
        response_text = await call_llm(prompt, temperature=0.1)
        # Strip markdown code fences if present (LLMs often wrap JSON in ```json ... ```)
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
            cleaned = cleaned.removeprefix("json").strip().strip("`").strip()
        edges = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Causal extraction returned non-JSON response", error=str(e))
        return []
    except Exception as e:
        logger.error("Failed to extract causal edges", error=str(e))
        return []

    if not edges:
        return []

    return await store_causal_edges(tenant_id, agent_id, edges)


# ─── D05: Store Causal Edges ──────────────────

async def store_causal_edges(
    tenant_id: UUID | None,
    agent_id: UUID,
    edges: list[dict],
) -> list[dict]:
    """Store explicit causal edges in the graph database.

    Args:
        edges: List of dicts containing from_memory_id, to_memory_id, relation, confidence, description.
    """
    stored_edges = []
    now = datetime.now(UTC).replace(tzinfo=None)
    tenant_id_to_use = tenant_id or uuid4()

    async with get_db_session_for_tenant(str(tenant_id_to_use)) as session:
        for edge in edges:
            try:
                edge_id = uuid4()
                await session.execute(
                    text("""
                    INSERT INTO causal_edges
                        (id, agent_id, tenant_id, from_memory_id, to_memory_id,
                         relation, confidence, description, created_at)
                    VALUES
                        (:id, :agent_id, :tenant_id, :from_id, :to_id,
                         :relation, :confidence, :desc, :now)
                    ON CONFLICT (from_memory_id, to_memory_id, relation) DO NOTHING
                    """),
                    {
                        "id": edge_id,
                        "agent_id": agent_id,
                        "tenant_id": tenant_id_to_use,
                        "from_id": edge["from_memory_id"],
                        "to_id": edge["to_memory_id"],
                        "relation": edge.get("relation", "causes"),
                        "confidence": edge.get("confidence", 1.0),
                        "desc": edge.get("description", ""),
                        "now": now,
                    },
                )
                stored_edges.append(edge)
            except Exception as e:
                logger.warning("Skipped storing causal edge", error=str(e), edge=edge)

    if stored_edges:
        logger.info(
            "Stored causal edges",
            agent_id=str(agent_id),
            count=len(stored_edges),
        )

    return stored_edges


# ─── D06: Causal Chain Traversal ──────────────

async def traverse_causal_chain(
    agent_id: UUID,
    memory_id: UUID,
    max_depth: int = 3,
    direction: str = "both",
) -> dict:
    """Traverse the causal graph starting from a specific memory.

    Returns the 'ancestry' (causes) and/or 'descendants' (effects) of a memory.

    Args:
        agent_id: The agent ID.
        memory_id: The starting memory node.
        max_depth: How many hops to traverse.
        direction: 'causes' (upstream), 'effects' (downstream), or 'both'.

    Returns:
        Graph dictionary with nodes and edges.
    """
    nodes = {}
    edges = []

    async with get_db_session() as session:
        # First, get the starting node
        for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
            result = await session.execute(
                text(f"SELECT id, content FROM {table} WHERE id = :id AND agent_id = :agent_id"),
                {"id": memory_id, "agent_id": agent_id}
            )
            row = result.fetchone()
            if row:
                nodes[str(row.id)] = {"id": str(row.id), "content": row.content}
                break

        if not nodes:
            return {"nodes": [], "edges": []}

        # Recursive CTE for graph traversal
        # We need upstream (causes) and downstream (effects)

        if direction in ("causes", "both"):
            # Find what caused this memory (upstream)
            result = await session.execute(
                text("""
                WITH RECURSIVE causal_tree AS (
                    SELECT from_memory_id, to_memory_id, relation, confidence, description, 1 as depth
                    FROM causal_edges
                    WHERE to_memory_id = :start_id AND agent_id = :agent_id

                    UNION ALL

                    SELECT ce.from_memory_id, ce.to_memory_id, ce.relation, ce.confidence, ce.description, ct.depth + 1
                    FROM causal_edges ce
                    JOIN causal_tree ct ON ce.to_memory_id = ct.from_memory_id
                    WHERE ce.agent_id = :agent_id AND ct.depth < :max_depth
                )
                SELECT * FROM causal_tree
                """),
                {"start_id": memory_id, "agent_id": agent_id, "max_depth": max_depth}
            )
            for row in result.fetchall():
                edges.append({
                    "from": str(row.from_memory_id),
                    "to": str(row.to_memory_id),
                    "relation": row.relation,
                    "confidence": row.confidence,
                    "description": row.description,
                    "direction": "upstream",
                    "depth": row.depth
                })

        if direction in ("effects", "both"):
            # Find what this memory caused (downstream)
            result = await session.execute(
                text("""
                WITH RECURSIVE causal_tree AS (
                    SELECT from_memory_id, to_memory_id, relation, confidence, description, 1 as depth
                    FROM causal_edges
                    WHERE from_memory_id = :start_id AND agent_id = :agent_id

                    UNION ALL

                    SELECT ce.from_memory_id, ce.to_memory_id, ce.relation, ce.confidence, ce.description, ct.depth + 1
                    FROM causal_edges ce
                    JOIN causal_tree ct ON ce.from_memory_id = ct.to_memory_id
                    WHERE ce.agent_id = :agent_id AND ct.depth < :max_depth
                )
                SELECT * FROM causal_tree
                """),
                {"start_id": memory_id, "agent_id": agent_id, "max_depth": max_depth}
            )
            for row in result.fetchall():
                edges.append({
                    "from": str(row.from_memory_id),
                    "to": str(row.to_memory_id),
                    "relation": row.relation,
                    "confidence": row.confidence,
                    "description": row.description,
                    "direction": "downstream",
                    "depth": row.depth
                })

        # Fetch missing node contents
        missing_nodes = set()
        for e in edges:
            missing_nodes.add(e["from"])
            missing_nodes.add(e["to"])

        missing_nodes -= set(nodes.keys())

        if missing_nodes:
            missing_ids = list(missing_nodes)
            for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
                result = await session.execute(
                    text(f"SELECT id, content FROM {table} WHERE id = ANY(:ids::uuid[])"),
                    {"ids": missing_ids}
                )
                for row in result.fetchall():
                    nodes[str(row.id)] = {"id": str(row.id), "content": row.content}

    return {
        "nodes": list(nodes.values()),
        "edges": edges,
    }


# ─── D09: Causal Frequency Analysis ───────────

async def analyze_causal_frequencies(
    agent_id: UUID,
    effect_theme: str,
    embedder: Any,
    limit: int = 50,
) -> dict:
    """Analyze what causes a specific type of event across the entire memory.

    1. Embed the effect_theme (e.g., "customer churn").
    2. Find memories that semantically match this theme.
    3. Traverse upstream (causes) for those memories.
    4. Use an LLM to group and count the root causes.
    """
    query_embedding = embedder.embed(effect_theme)

    async with get_db_session() as session:
        # Find episodic memories matching the effect theme
        result = await session.execute(
            text("""
            SELECT id, content, 1 - (embedding <=> :embedding) AS sim
            FROM episodic_memories
            WHERE agent_id = :agent_id AND deleted_at IS NULL
            ORDER BY sim DESC
            LIMIT :limit
            """),
            {
                "agent_id": agent_id,
                "embedding": query_embedding,
                "limit": limit
            }
        )
        effect_memories = result.fetchall()

    if not effect_memories:
        return {"theme": effect_theme, "causes": []}

    # Find causes for these effects
    all_causes = []
    for mem in effect_memories:
        graph = await traverse_causal_chain(agent_id, mem.id, max_depth=1, direction="causes")
        # Find upstream nodes
        for edge in graph["edges"]:
            if edge["direction"] == "upstream":
                cause_id = edge["from"]
                cause_node = next((n for n in graph["nodes"] if n["id"] == cause_id), None)
                if cause_node:
                    all_causes.append(cause_node["content"])

    if not all_causes:
        return {"theme": effect_theme, "causes": []}

    # Use LLM to group and summarize frequencies
    prompt = f"""
    Analyze the following list of root causes for the theme: "{effect_theme}".
    Group similar causes together and calculate their frequency.

    Raw Causes:
    {json.dumps(all_causes, indent=2)}

    Respond ONLY with a JSON array of objects, sorted by frequency (descending).
    Format:
    [
      {{"cause_summary": "Poor customer service", "frequency": 5, "percentage": 50.0}},
      {{"cause_summary": "High pricing", "frequency": 3, "percentage": 30.0}}
    ]
    """

    try:
        response_text = await call_llm(prompt, temperature=0.0)
        cleaned = response_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```", 2)[-1] if cleaned.count("```") >= 2 else cleaned
            cleaned = cleaned.removeprefix("json").strip().strip("`").strip()
        frequencies = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.warning("Frequency analysis returned non-JSON response", error=str(e))
        return {"theme": effect_theme, "causes": [], "error": "LLM returned non-JSON response"}
    except Exception as e:
        logger.error("Failed to analyze causal frequencies", error=str(e))
        return {"theme": effect_theme, "causes": [], "error": str(e)}

    return {
        "theme": effect_theme,
        "analyzed_effects_count": len(effect_memories),
        "total_causes_found": len(all_causes),
        "causes": frequencies
    }

