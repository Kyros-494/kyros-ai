"""D08: Causal Graph API Endpoints."""

from uuid import UUID

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session_for_tenant

router = APIRouter()
logger = get_logger("kyros.api.causal")


class CausalExplainRequest(BaseModel):
    agent_id: str
    memory_id: UUID
    max_depth: int = Field(default=3, ge=1, le=10)
    direction: str = Field(default="both", description="'causes', 'effects', or 'both'")


@router.post("/explain")
async def explain_memory(request: Request, body: CausalExplainRequest) -> dict[str, any]:
    """Explain why a memory happened (causal chain traversal)."""
    from kyros.intelligence.causal import traverse_causal_chain

    if body.direction not in ("causes", "effects", "both"):
        raise HTTPException(
            status_code=400, detail="direction must be 'causes', 'effects', or 'both'"
        )

    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, body.agent_id)

        graph = await traverse_causal_chain(
            agent_id=agent_id_internal,
            memory_id=body.memory_id,
            max_depth=body.max_depth,
            direction=body.direction,
        )
    except SQLAlchemyError as e:
        logger.error("DB error in explain_memory", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in explain_memory", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e

    if not graph["nodes"]:
        raise HTTPException(status_code=404, detail="Memory not found or has no causal links")

    return {"agent_id": body.agent_id, "memory_id": str(body.memory_id), "graph": graph}


class CausalFrequencyRequest(BaseModel):
    agent_id: str
    theme: str = Field(
        ..., min_length=1, description="The effect to analyze (e.g., 'customer churn')"
    )
    limit: int = Field(default=50, ge=1, le=200)


@router.post("/frequent-causes")
async def frequent_causes(request: Request, body: CausalFrequencyRequest) -> dict[str, any]:
    """Analyze what causes a specific type of event across all memories."""
    from kyros.intelligence.causal import analyze_causal_frequencies

    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, body.agent_id)

        result = await analyze_causal_frequencies(
            agent_id=agent_id_internal,
            effect_theme=body.theme,
            embedder=request.app.state.embedder,
            limit=body.limit,
        )
    except SQLAlchemyError as e:
        logger.error("DB error in frequent_causes", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in frequent_causes", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e

    return {"agent_id": body.agent_id, **result}


@router.get("/graph/{agent_id}")
async def get_causal_graph(agent_id: str, request: Request, limit: int = 100) -> dict[str, any]:
    """Return the agent's causal graph for D3/Cytoscape frontend rendering."""
    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)

            result = await session.execute(
                text("""
                SELECT from_memory_id, to_memory_id, relation, confidence, description
                FROM causal_edges
                WHERE agent_id = :agent_id
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"agent_id": agent_id_internal, "limit": limit},
            )
            edges = []
            node_ids: set[str] = set()
            for row in result.fetchall():
                edges.append(
                    {
                        "source": str(row.from_memory_id),
                        "target": str(row.to_memory_id),
                        "relation": row.relation,
                        "confidence": row.confidence,
                        "description": row.description,
                    }
                )
                node_ids.add(str(row.from_memory_id))
                node_ids.add(str(row.to_memory_id))

            nodes = []
            if node_ids:
                for table in ["episodic_memories", "semantic_memories", "procedural_memories"]:
                    res = await session.execute(
                        text(f"SELECT id, content FROM {table} WHERE id = ANY(:ids::uuid[])"),
                        {"ids": list(node_ids)},
                    )
                    for r in res.fetchall():
                        nodes.append(
                            {
                                "id": str(r.id),
                                "label": r.content[:50] + ("..." if len(r.content) > 50 else ""),
                                "full_content": r.content,
                            }
                        )

    except SQLAlchemyError as e:
        logger.error("DB error in get_causal_graph", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in get_causal_graph", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e

    return {"agent_id": agent_id, "nodes": nodes, "edges": edges}
