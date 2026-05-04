"""Semantic memory routes — store and query facts (knowledge graph)."""

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.schemas.memory import FactResult, RecallRequest, RecallResponse, StoreFactRequest
from kyros.storage.postgres import get_db_session_for_tenant

router = APIRouter()
logger = get_logger("kyros.api.semantic")


@router.post("/facts", response_model=FactResult, status_code=201)
async def store_fact(request: Request, body: StoreFactRequest):
    """Store a semantic fact (subject-predicate-object triple) with contradiction detection."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.store_fact(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in store_fact", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in store_fact", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.post("/query", response_model=RecallResponse)
async def query_facts(request: Request, body: RecallRequest):
    """Query the semantic knowledge graph via natural language."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.query_semantic_facts(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in query_facts", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in query_facts", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/graph/{agent_id}")
async def get_semantic_graph(agent_id: str, request: Request, limit: int = 100):
    """Return the agent's semantic belief graph for frontend rendering (D3/Cytoscape)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)

            result = await session.execute(
                text("""
                SELECT from_fact_id, to_fact_id, relatedness_score
                FROM semantic_edges
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
                        "source": str(row.from_fact_id),
                        "target": str(row.to_fact_id),
                        "relatedness": row.relatedness_score,
                    }
                )
                node_ids.add(str(row.from_fact_id))
                node_ids.add(str(row.to_fact_id))

            nodes = []
            if node_ids:
                res = await session.execute(
                    text("""
                    SELECT id, subject, predicate, object, confidence
                    FROM semantic_memories
                    WHERE id = ANY(:ids::uuid[]) AND deleted_at IS NULL
                    """),
                    {"ids": list(node_ids)},
                )
                for r in res.fetchall():
                    nodes.append(
                        {
                            "id": str(r.id),
                            "label": f"{r.subject} {r.predicate} {r.object}",
                            "confidence": r.confidence,
                        }
                    )

        return {"agent_id": agent_id, "nodes": nodes, "edges": edges}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in get_semantic_graph", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in get_semantic_graph", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e
