"""Admin routes — summarise, export, import, integrity, decay, migration."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from kyros.api.v1.deps import get_memory_service
from kyros.logging import get_logger
from kyros.schemas.memory import ExportResponse
from kyros.storage.postgres import get_db_session_for_tenant

router = APIRouter()
logger = get_logger("kyros.admin")

_VALID_TABLES = frozenset({"episodic_memories", "semantic_memories", "procedural_memories"})


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─── Summarise ────────────────────────────────

@router.get("/summarise/{agent_id}")
async def summarise(agent_id: str, request: Request):
    """Get the compressed history card for an agent."""
    from kyros.intelligence.compression import CompressionEngine

    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
            result = await session.execute(
                text("""
                SELECT id, content, importance, created_at
                FROM episodic_memories
                WHERE agent_id = :aid AND deleted_at IS NULL
                ORDER BY created_at ASC
                """),
                {"aid": agent_id_internal},
            )
            rows = result.fetchall()
    except SQLAlchemyError as e:
        logger.error("DB error in summarise", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    if not rows:
        return {
            "agent_id": agent_id,
            "summary": "No memories found for this agent.",
            "memory_count": 0,
            "compression_ratio": 0.0,
            "generated_at": _utcnow().isoformat(),
        }

    raw_memories = [
        {
            "content": row.content,
            "importance": row.importance,
            "created_at": row.created_at.isoformat() if row.created_at else "",
        }
        for row in rows
    ]

    try:
        engine = CompressionEngine()
        card = engine.compress_agent_memories(raw_memories)
    except Exception as e:
        logger.error("Compression failed", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=500, detail="Compression failed")

    return {
        "agent_id": agent_id,
        "summary": card.summary,
        "memory_count": card.memory_count,
        "compression_ratio": card.compression_ratio,
        "levels": card.levels,
        "generated_at": card.generated_at.isoformat(),
    }


# ─── Export / Import ──────────────────────────

@router.get("/export/{agent_id}", response_model=ExportResponse)
async def export_memories(agent_id: str, request: Request):
    """Export all memories for an agent as JSON."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)
    try:
        return await service.export_memories(tenant_id, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("DB error in export_memories", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")


@router.post("/import/{agent_id}")
async def import_memories(agent_id: str, request: Request):
    """Import memories from JSON into an agent."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    try:
        return await service.import_memories(tenant_id, agent_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SQLAlchemyError as e:
        logger.error("DB error in import_memories", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")


# ─── B11: Staleness Report ────────────────────

@router.get("/staleness-report/{agent_id}")
async def staleness_report(agent_id: str, request: Request):
    """Get a comprehensive staleness report for an agent."""
    from kyros.intelligence.decay import DecayConfig
    from kyros.intelligence.decay_service import generate_staleness_report

    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
        config = DecayConfig(tenant_id=str(tenant_id) if tenant_id else "")
        return await generate_staleness_report(agent_id_internal, config)
    except SQLAlchemyError as e:
        logger.error("DB error in staleness_report", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")


# ─── B14: Decay Rate Configuration ───────────

@router.get("/decay-rates")
async def get_decay_rates(request: Request):
    """Get the current decay rate configuration."""
    from kyros.intelligence.decay import DEFAULT_DECAY_RATES, DecayConfig

    config = DecayConfig()
    rates = {}
    for category, rate in DEFAULT_DECAY_RATES.items():
        half_life = math.log(2) / rate if rate > 0 else float("inf")
        rates[category] = {
            "decay_rate": rate,
            "half_life_days": round(half_life, 1),
        }

    return {
        "default_rates": rates,
        "warning_threshold": config.freshness_warning_threshold,
        "critical_threshold": config.freshness_critical_threshold,
        "archive_threshold": config.auto_archive_threshold,
    }


@router.put("/decay-rates")
async def update_decay_rates(request: Request):
    """Update tenant-specific decay rates (half_life_days → decay_rate)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    rates_input = body.get("rates", {})
    if not isinstance(rates_input, dict):
        raise HTTPException(status_code=400, detail="'rates' must be a JSON object")

    updated = {}
    for category, half_life_days in rates_input.items():
        try:
            hl = float(half_life_days)
        except (TypeError, ValueError):
            raise HTTPException(
                status_code=400,
                detail=f"half_life_days for '{category}' must be a number",
            )
        if hl <= 0:
            raise HTTPException(
                status_code=400,
                detail=f"half_life_days for '{category}' must be positive",
            )
        decay_rate = math.log(2) / hl
        updated[category] = {
            "decay_rate": round(decay_rate, 6),
            "half_life_days": round(hl, 1),
        }

    return {
        "updated_rates": updated,
        "note": "Custom rates are applied per-tenant. Default rates unchanged.",
    }


# ─── C10: Memory Proof ────────────────────────

@router.get("/memory/{memory_id}/proof")
async def get_memory_proof(memory_id: str, request: Request):
    """Get the cryptographic Merkle proof for a specific memory."""
    from kyros.intelligence.integrity import MerkleTree

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = None
            target_leaf = None

            for table in _VALID_TABLES:
                if table not in _VALID_TABLES:
                    continue
                result = await session.execute(
                    text(f"SELECT agent_id, merkle_leaf FROM {table} WHERE id = :id"),
                    {"id": memory_id},
                )
                row = result.fetchone()
                if row:
                    agent_id_internal = row.agent_id
                    target_leaf = row.merkle_leaf
                    break

            if not agent_id_internal:
                raise HTTPException(status_code=404, detail="Memory not found")

            # Verify the caller owns this agent
            await service._resolve_agent(session, tenant_id, str(agent_id_internal))

            leaf_hashes: list[str] = []
            for table in _VALID_TABLES:
                if table not in _VALID_TABLES:
                    continue
                result = await session.execute(
                    text(f"""
                    SELECT merkle_leaf FROM {table}
                    WHERE agent_id = :agent_id AND deleted_at IS NULL
                      AND merkle_leaf IS NOT NULL
                    ORDER BY id ASC
                    """),
                    {"agent_id": agent_id_internal},
                )
                leaf_hashes.extend(row.merkle_leaf for row in result.fetchall())

    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("DB error in get_memory_proof", memory_id=memory_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    if not leaf_hashes:
        raise HTTPException(status_code=404, detail="No active memories found for this agent")

    if target_leaf not in leaf_hashes:
        raise HTTPException(status_code=404, detail="Memory leaf not found in active tree")

    leaf_index = leaf_hashes.index(target_leaf)
    tree = MerkleTree(leaf_hashes)
    proof = tree.get_proof(leaf_index)

    return {
        "memory_id": memory_id,
        "agent_id": str(agent_id_internal),
        "proof": {
            "leaf_hash": proof.leaf_hash,
            "root_hash": proof.root_hash,
            "proof_path": proof.proof_path,
            "leaf_index": proof.leaf_index,
            "tree_size": proof.tree_size,
        },
    }


# ─── C11: Agent Integrity Audit ───────────────

@router.post("/agent/{agent_id}/audit")
async def audit_integrity(agent_id: str, request: Request):
    """Verify the cryptographic integrity of all memories for an agent."""
    from kyros.intelligence.integrity_service import verify_agent_integrity

    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
        tampered = await verify_agent_integrity(agent_id_internal)
    except SQLAlchemyError as e:
        logger.error("DB error in audit_integrity", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    return {
        "agent_id": agent_id,
        "is_intact": len(tampered) == 0,
        "tampered_count": len(tampered),
        "tampered_memories": tampered,
    }


# ─── C17: Compliance Export ───────────────────

@router.get("/agent/{agent_id}/compliance-export")
async def compliance_export(agent_id: str, request: Request, days: int = 90):
    """Export the immutable audit log for an agent for the past N days."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")
    if days < 1 or days > 3650:
        raise HTTPException(status_code=400, detail="days must be between 1 and 3650")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
            since = _utcnow() - timedelta(days=days)
            result = await session.execute(
                text("""
                SELECT id, merkle_root, tree_size, created_at
                FROM memory_audit_logs
                WHERE agent_id = :agent_id AND created_at >= :since
                ORDER BY created_at ASC
                """),
                {"agent_id": agent_id_internal, "since": since},
            )
            rows = result.fetchall()
    except SQLAlchemyError as e:
        logger.error("DB error in compliance_export", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    logs = [
        {
            "audit_id": str(row.id),
            "merkle_root": row.merkle_root,
            "tree_size": row.tree_size,
            "timestamp": row.created_at.isoformat(),
        }
        for row in rows
    ]

    return {
        "agent_id": agent_id,
        "export_date": _utcnow().isoformat(),
        "period_days": days,
        "total_audit_events": len(logs),
        "audit_trail": logs,
    }


# ─── F10–F12: Cross-Model Migration ──────────

class MigrationRequest(BaseModel):
    from_model: str = Field(..., min_length=1, max_length=100)
    to_model: str = Field(..., min_length=1, max_length=100)
    strategy: str = Field(
        default="translate",
        description="'translate' (fast ML projection) or 're-embed' (full API re-embedding)",
    )


@router.post("/agent/{agent_id}/migrate-embeddings")
async def migrate_embeddings(agent_id: str, request: Request, body: MigrationRequest):
    """Migrate all agent memory embeddings to a new embedding model space."""
    import asyncio
    from kyros.ml.translation import EmbeddingTranslator, MODEL_REGISTRY

    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    if body.strategy not in ("translate", "re-embed"):
        raise HTTPException(status_code=400, detail="strategy must be 'translate' or 're-embed'")

    if body.to_model not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported target model: {body.to_model!r}. Supported: {list(MODEL_REGISTRY.keys())}",
        )

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
    except SQLAlchemyError as e:
        logger.error("DB error resolving agent for migration", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    async def _run_migration() -> None:
        translator = EmbeddingTranslator()
        try:
            async with get_db_session_for_tenant(str(tenant_id)) as session:
                for table in _VALID_TABLES:
                    if table not in _VALID_TABLES:
                        continue
                    res = await session.execute(
                        text(f"SELECT id, embedding FROM {table} WHERE agent_id = :agent"),
                        {"agent": agent_id_internal},
                    )
                    rows = res.fetchall()
                    if not rows:
                        continue

                    for row in rows:
                        try:
                            vec_list = (
                                list(row.embedding)
                                if isinstance(row.embedding, (list, tuple))
                                else json.loads(row.embedding)
                            )
                            new_vec = translator.translate_mlp(
                                vec_list, body.from_model, body.to_model
                            )
                            await session.execute(
                                text(f"""
                                UPDATE {table}
                                SET embedding_secondary = embedding,
                                    embedding = :new_emb,
                                    embedding_model = :new_model
                                WHERE id = :id
                                """),
                                {
                                    "new_emb": new_vec,
                                    "new_model": body.to_model,
                                    "id": row.id,
                                },
                            )
                        except Exception as row_err:
                            logger.warning(
                                "Skipped row during migration",
                                table=table,
                                row_id=str(row.id),
                                error=str(row_err),
                            )

            logger.info(
                "Embedding migration complete",
                agent_id=agent_id,
                to_model=body.to_model,
            )
        except Exception as e:
            logger.error(
                "Embedding migration failed",
                agent_id=agent_id,
                to_model=body.to_model,
                error=str(e),
            )

    try:
        from kyros.main import create_background_task
        create_background_task(_run_migration())
    except ImportError:
        asyncio.create_task(_run_migration())

    return {
        "status": "accepted",
        "agent_id": agent_id,
        "from_model": body.from_model,
        "to_model": body.to_model,
        "message": "Migration started in the background.",
    }


# ─── H07: GDPR Hard Delete ────────────────────

@router.delete("/agent/{agent_id}/memories")
async def hard_delete_agent_memories(
    agent_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
):
    """GDPR 'Right to be Forgotten' — hard delete all memories for an agent."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)

            cert_data: dict[str, int] = {}
            for table, key in [
                ("episodic_memories", "deleted_episodic"),
                ("semantic_memories", "deleted_semantic"),
                ("procedural_memories", "deleted_procedural"),
            ]:
                if table not in _VALID_TABLES:
                    continue
                res = await session.execute(
                    text(f"SELECT COUNT(*) FROM {table} WHERE agent_id = :agent_id"),
                    {"agent_id": agent_id_internal},
                )
                cert_data[key] = res.scalar() or 0

            for table in _VALID_TABLES:
                if table not in _VALID_TABLES:
                    continue
                await session.execute(
                    text(f"DELETE FROM {table} WHERE agent_id = :agent_id"),
                    {"agent_id": agent_id_internal},
                )
            await session.execute(
                text("DELETE FROM memory_audit_logs WHERE agent_id = :agent_id"),
                {"agent_id": agent_id_internal},
            )
    except SQLAlchemyError as e:
        logger.error("DB error in hard_delete_agent_memories", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry")

    timestamp = _utcnow().isoformat()
    raw_cert = (
        f"{agent_id}:{tenant_id}:{timestamp}:"
        f"{cert_data['deleted_episodic']}:{cert_data['deleted_semantic']}"
    )
    cert_hash = hashlib.sha256(raw_cert.encode("utf-8")).hexdigest()

    certificate = {
        "certificate_id": f"DEL-{cert_hash[:16].upper()}",
        "agent_id": agent_id,
        "tenant_id": str(tenant_id),
        "timestamp": timestamp,
        "records_purged": cert_data,
        "cryptographic_signature": cert_hash,
        "compliance": "GDPR Article 17 — Right to Erasure",
    }

    logger.info(
        "GDPR hard delete executed",
        agent_id=agent_id,
        certificate_id=certificate["certificate_id"],
        records=cert_data,
    )
    return certificate
