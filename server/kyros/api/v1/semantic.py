"""Semantic memory routes — store and query facts (knowledge graph)."""

from typing import Any

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
async def store_fact(request: Request, body: StoreFactRequest) -> FactResult:
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
async def query_facts(request: Request, body: RecallRequest) -> RecallResponse:
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
async def get_semantic_graph(agent_id: str, request: Request, limit: int = 100) -> dict[str, Any]:
    """Return the agent's semantic belief graph for frontend rendering (D3/Cytoscape)."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)

            # Retrieve active semantic memories for this agent
            mem_result = await session.execute(
                text("""
                SELECT id, subject, predicate, object, confidence
                FROM semantic_memories
                WHERE agent_id = :agent_id AND deleted_at IS NULL
                ORDER BY created_at DESC
                LIMIT :limit
                """),
                {"agent_id": agent_id_internal, "limit": limit},
            )
            
            nodes = []
            node_ids = []
            for r in mem_result.fetchall():
                nodes.append(
                    {
                        "id": str(r.id),
                        "label": f"{r.subject} {r.predicate} {r.object}",
                        "confidence": r.confidence,
                    }
                )
                node_ids.append(r.id)

            edges = []
            if node_ids:
                edge_result = await session.execute(
                    text("""
                    SELECT from_fact_id, to_fact_id, relatedness_score
                    FROM semantic_edges
                    WHERE agent_id = :agent_id
                      AND from_fact_id = ANY(CAST(:node_ids AS uuid[]))
                      AND to_fact_id = ANY(CAST(:node_ids AS uuid[]))
                    """),
                    {"agent_id": agent_id_internal, "node_ids": node_ids},
                )
                for row in edge_result.fetchall():
                    edges.append(
                        {
                            "source": str(row.from_fact_id),
                            "target": str(row.to_fact_id),
                            "relatedness": row.relatedness_score,
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


@router.put("/facts", response_model=FactResult)
async def upsert_fact(request: Request, body: StoreFactRequest) -> FactResult:
    """Upsert a semantic fact (subject-predicate-object triple) dynamically."""
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)
    try:
        return await service.store_fact(tenant_id=tenant_id, request=body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in upsert_fact", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in upsert_fact", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error") from e


@router.get("/entities/{agent_id}")
async def get_entities(agent_id: str, request: Request, limit: int = 100) -> dict[str, Any]:
    """Return the agent's resolved canonical entities and their properties."""
    import json
    tenant_id = getattr(request.state, "tenant_id", None)
    service = get_memory_service(request)

    if limit < 1 or limit > 1000:
        raise HTTPException(status_code=400, detail="limit must be between 1 and 1000")

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)

            # Retrieve entities for this agent
            ent_result = await session.execute(
                text("""
                SELECT id, name, canonical_name, state, created_at, updated_at
                FROM entities
                WHERE agent_id = :agent_id AND deleted_at IS NULL
                ORDER BY updated_at DESC
                LIMIT :limit
                """),
                {"agent_id": agent_id_internal, "limit": limit},
            )
            
            # Get term counts and avg confidence to calculate memory_count/source_count/confidence
            stats_result = await session.execute(
                text("""
                SELECT term, SUM(cnt) as total_count, AVG(avg_c) as avg_confidence FROM (
                    SELECT subject as term, COUNT(*) as cnt, AVG(confidence) as avg_c FROM semantic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL AND valid_to IS NULL
                    GROUP BY subject
                    UNION ALL
                    SELECT object as term, COUNT(*) as cnt, AVG(confidence) as avg_c FROM semantic_memories
                    WHERE agent_id = :agent_id AND deleted_at IS NULL AND valid_to IS NULL
                    GROUP BY object
                ) as term_stats
                GROUP BY term
                """),
                {"agent_id": agent_id_internal}
            )
            term_stats_map = {}
            for row in stats_result.fetchall():
                if row.term:
                    term_stats_map[row.term.lower()] = (int(row.total_count), float(row.avg_confidence or 1.0))

            entities = []
            for r in ent_result.fetchall():
                ent_state = r.state
                if isinstance(ent_state, str):
                    try:
                        ent_state = json.loads(ent_state)
                    except Exception:
                        ent_state = {}
                elif ent_state is None:
                    ent_state = {}

                ent_type = ent_state.get("type") or ent_state.get("entity_type") or "Other"
                aliases = ent_state.get("aliases") or ent_state.get("alias") or []
                if isinstance(aliases, str):
                    aliases = [aliases]
                if r.canonical_name and r.name and r.canonical_name.lower() != r.name.lower():
                    if r.name not in aliases:
                        aliases.append(r.name)

                name_lower = r.name.lower() if r.name else ""
                canon_lower = r.canonical_name.lower() if r.canonical_name else ""

                stats1 = term_stats_map.get(name_lower, (0, 0.95))
                stats2 = term_stats_map.get(canon_lower, (0, 0.95)) if canon_lower and canon_lower != name_lower else (0, 0.95)

                mem_count = stats1[0] + stats2[0]
                if mem_count == 0:
                    mem_count = 1

                avg_conf = (stats1[1] + stats2[1]) / 2.0 if stats1[0] > 0 and stats2[0] > 0 else (stats1[1] if stats1[0] > 0 else stats2[1])

                entities.append(
                    {
                        "id": str(r.id),
                        "name": r.name,
                        "canonical_name": r.canonical_name,
                        "entity_type": ent_type,
                        "type": ent_type,
                        "aliases": aliases,
                        "confidence": avg_conf,
                        "score": avg_conf,
                        "memory_count": mem_count,
                        "source_count": mem_count,
                        "first_seen": r.created_at.isoformat() if r.created_at else None,
                        "state": ent_state,
                        "created_at": r.created_at.isoformat() if r.created_at else None,
                        "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                    }
                )

        return {"agent_id": agent_id, "entities": entities}

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in get_entities", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e
    except Exception as e:
        logger.error("Unexpected error in get_entities", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e
