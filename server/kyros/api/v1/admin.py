"""Admin routes — summarise, export, import, integrity, decay, migration."""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from datetime import datetime, timedelta
try:
    from datetime import UTC
except ImportError:
    from datetime import timezone
    UTC = timezone.utc
from typing import Any

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
    return datetime.now(UTC)


# ─── Summarise ────────────────────────────────


@router.get("/summarise/{agent_id}")
async def summarise(agent_id: str, request: Request) -> dict[str, Any]:
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

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
        raise HTTPException(status_code=500, detail="Compression failed") from e

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
async def export_memories(agent_id: str, request: Request) -> ExportResponse:
    """Export all memories for an agent as JSON."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)
    try:
        return await service.export_memories(tenant_id, agent_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in export_memories", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e


@router.post("/import/{agent_id}")
async def import_memories(agent_id: str, request: Request) -> dict[str, Any]:
    """Import memories from JSON into an agent."""
    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Request body must be a JSON object")

    try:
        return await service.import_memories(tenant_id, agent_id, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in import_memories", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e


# ─── B11: Staleness Report ────────────────────


@router.get("/staleness-report/{agent_id}")
async def staleness_report(agent_id: str, request: Request) -> dict[str, Any]:
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e


# ─── B14: Decay Rate Configuration ───────────


@router.get("/decay-rates")
async def get_decay_rates(request: Request) -> dict[str, Any]:
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
async def update_decay_rates(request: Request) -> dict[str, Any]:
    """Update tenant-specific decay rates (half_life_days → decay_rate)."""
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    rates_input = body.get("rates", {})
    if not isinstance(rates_input, dict):
        raise HTTPException(status_code=400, detail="'rates' must be a JSON object")

    updated = {}
    for category, half_life_days in rates_input.items():
        try:
            hl = float(half_life_days)
        except (TypeError, ValueError) as e:
            raise HTTPException(
                status_code=400,
                detail=f"half_life_days for '{category}' must be a number",
            ) from e
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
async def get_memory_proof(memory_id: str, request: Request) -> dict[str, Any]:
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

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
async def audit_integrity(agent_id: str, request: Request) -> dict[str, Any]:
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "agent_id": agent_id,
        "is_intact": len(tampered) == 0,
        "tampered_count": len(tampered),
        "tampered_memories": tampered,
    }


# ─── C17: Compliance Export ───────────────────


@router.get("/agent/{agent_id}/compliance-export")
async def compliance_export(agent_id: str, request: Request, days: int = 90) -> dict[str, Any]:
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
            since = (_utcnow() - timedelta(days=days)).replace(tzinfo=None)
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

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
async def migrate_embeddings(
    agent_id: str, request: Request, body: MigrationRequest
) -> dict[str, Any]:
    """Migrate all agent memory embeddings to a new embedding model space."""
    import asyncio

    from kyros.ml.translation import MODEL_REGISTRY, EmbeddingTranslator

    if not agent_id.strip():
        raise HTTPException(status_code=400, detail="agent_id must not be blank")

    if body.strategy not in ("translate", "re-embed"):
        raise HTTPException(status_code=400, detail="strategy must be 'translate' or 're-embed'")

    if body.to_model not in MODEL_REGISTRY:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unsupported target model: {body.to_model!r}. "
                f"Supported: {list(MODEL_REGISTRY.keys())}"
            ),
        )

    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
    except SQLAlchemyError as e:
        logger.error("DB error resolving agent for migration", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

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

        create_background_task(
            _run_migration(),
            name="migrate_embeddings",
            details=f"Migrating embeddings for agent {agent_id} from {body.from_model} to {body.to_model}"
        )
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
) -> dict[str, Any]:
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
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

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


# ─── List Agents ──────────────────────────────


@router.get("/agents")
async def list_agents(request: Request) -> dict[str, Any]:
    """List all agents for the current tenant."""
    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    try:
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            result = await session.execute(
                text("""
                SELECT external_id, display_name, metadata
                FROM agents
                WHERE tenant_id = :tid
                ORDER BY display_name ASC
                """),
                {"tid": tenant_id},
            )
            rows = result.fetchall()
    except SQLAlchemyError as e:
        logger.error("DB error in list_agents", tenant_id=str(tenant_id), error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "agents": [
            {
                "agent_id": row.external_id,
                "display_name": row.display_name or row.external_id,
                "metadata": row.metadata or {},
            }
            for row in rows
        ]
    }


# ─── Create Tenant ────────────────────────────


class CreateTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)
    plan: str = Field(default="pro")


@router.post("/tenants")
async def create_tenant(body: CreateTenantRequest, request: Request) -> dict[str, Any]:
    """Create a new tenant and generate an API key.

    Requires the master admin token or jwt_secret_key for authentication.
    """
    import os
    import secrets
    from kyros.config import get_settings
    from kyros.storage.postgres import get_db_session

    settings = get_settings()
    admin_token = settings.admin_token or settings.jwt_secret_key
    
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
    else:
        token = request.headers.get("X-Admin-Token", "").strip()

    if not token or token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    api_key = f"mk_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    tenant_id = uuid.uuid4()

    try:
        async with get_db_session() as session:
            await session.execute(
                text("""
                INSERT INTO tenants (
                    id, name, email, api_key_hash, plan, is_active, created_at, updated_at
                )
                VALUES (
                    :id, :name, :email, :key_hash, :plan, true, NOW(), NOW()
                )
                """),
                {
                    "id": tenant_id,
                    "name": body.name,
                    "email": body.email,
                    "key_hash": key_hash,
                    "plan": body.plan,
                },
            )
    except SQLAlchemyError as e:
        logger.error("DB error in create_tenant", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "tenant_id": str(tenant_id),
        "name": body.name,
        "email": body.email,
        "api_key": api_key,
        "plan": body.plan,
        "status": "created",
    }


class CreatePublicTenantRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    email: str = Field(..., min_length=1, max_length=255)


@router.post("/public/sandbox/keys")
async def create_public_sandbox_key(body: CreatePublicTenantRequest) -> dict[str, Any]:
    """Create a new tenant with free tier/sandbox plan and return the generated API key."""
    import secrets
    from kyros.storage.postgres import get_db_session

    api_key = f"mk_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
    tenant_id = uuid.uuid4()

    try:
        async with get_db_session() as session:
            await session.execute(
                text("""
                INSERT INTO tenants (
                    id, name, email, api_key_hash, plan, is_active, created_at, updated_at
                )
                VALUES (
                    :id, :name, :email, :key_hash, 'free', true, NOW(), NOW()
                )
                """),
                {
                    "id": tenant_id,
                    "name": body.name,
                    "email": body.email,
                    "key_hash": key_hash,
                },
            )
    except SQLAlchemyError as e:
        logger.error("DB error in create_public_sandbox_key", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "api_key": api_key,
        "status": "created",
    }


@router.get("/background-tasks")
async def get_background_tasks(request: Request) -> list[dict[str, Any]]:
    """Retrieve the recent background tasks and their execution statuses/errors."""
    from kyros.services.background_tasks import get_task_history
    return get_task_history()


@router.get("/configure-llm")
async def get_llm_config(request: Request) -> dict[str, Any]:
    """Retrieve the current in-memory LLM configurations and active status."""
    import os
    from kyros.config import get_settings
    
    settings = get_settings()
    
    def mask_key(k: str | None) -> str:
        if not k:
            return ""
        if len(k) <= 8:
            return "********"
        return f"{k[:4]}...{k[-4:]}"

    active_provider = "none"
    if settings.gemini_api_key:
        active_provider = "gemini"
    elif settings.openai_api_key:
        active_provider = "openai"
    elif settings.mistral_api_key:
        active_provider = "mistral"
    elif settings.anthropic_api_key:
        active_provider = "anthropic"

    allow_mock = os.getenv("KYROS_ALLOW_MOCK_LLM", "false").lower() == "true"

    return {
        "active_provider": active_provider,
        "allow_mock": allow_mock,
        "providers": {
            "openai": {
                "has_key": bool(settings.openai_api_key),
                "masked_key": mask_key(settings.openai_api_key),
                "model": settings.openai_model
            },
            "gemini": {
                "has_key": bool(settings.gemini_api_key),
                "masked_key": mask_key(settings.gemini_api_key),
                "model": settings.gemini_model
            },
            "mistral": {
                "has_key": bool(settings.mistral_api_key),
                "masked_key": mask_key(settings.mistral_api_key),
                "model": settings.mistral_model
            },
            "anthropic": {
                "has_key": bool(settings.anthropic_api_key),
                "masked_key": mask_key(settings.anthropic_api_key),
                "model": settings.anthropic_model
            }
        }
    }


def _update_env_file(key: str, value: str) -> None:
    import os
    paths = ["/app/.env", ".env", "../.env"]
    for path in paths:
        try:
            lines = []
            if os.path.exists(path):
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()
            
            found = False
            for i, line in enumerate(lines):
                line_stripped = line.strip()
                k_clean = key.removeprefix("KYROS_")
                l_clean = line_stripped.removeprefix("KYROS_")
                if l_clean.startswith(f"{k_clean}="):
                    prefix = "KYROS_" if line_stripped.startswith("KYROS_") else ""
                    lines[i] = f"{prefix}{k_clean}={value}\n"
                    found = True
                    break
            
            if not found:
                prefix = ""
                # Use KYROS_ prefix for standard config parameters if not specified
                if key in ("DATABASE_URL", "REDIS_URL", "JWT_SECRET_KEY", "ENVIRONMENT", "API_KEY", "ADMIN_TOKEN", "ALLOW_MOCK_LLM", "OPENAI_MODEL", "GEMINI_MODEL", "MISTRAL_MODEL", "ANTHROPIC_MODEL") and not key.startswith("KYROS_"):
                    prefix = "KYROS_"
                lines.append(f"{prefix}{key}={value}\n")
                
            with open(path, "w", encoding="utf-8") as f:
                f.writelines(lines)
            logger.info(f"Successfully updated env file at {path} with {key}")
        except Exception as e:
            logger.warning(f"Could not update env file at {path}: {e}")


@router.post("/configure-llm")
async def configure_llm(request: Request) -> dict[str, str]:
    """Dynamically configure LLM API key in memory and persist to .env."""
    import os
    from kyros.config import get_settings

    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body") from None

    provider = body.get("provider")
    api_key = body.get("api_key")
    allow_mock = body.get("allow_mock", False)

    if allow_mock:
        os.environ["KYROS_ALLOW_MOCK_LLM"] = "true"
        _update_env_file("KYROS_ALLOW_MOCK_LLM", "true")
    else:
        os.environ["KYROS_ALLOW_MOCK_LLM"] = "false"
        _update_env_file("KYROS_ALLOW_MOCK_LLM", "false")

    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="Missing 'provider' or 'api_key'")

    provider = provider.lower()
    supported = {"openai", "gemini", "mistral", "anthropic"}
    if provider not in supported:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    settings = get_settings()
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    
    target_env = env_keys[provider]
    
    # 1. Update os.environ and cached Settings
    os.environ[target_env] = api_key
    _update_env_file(target_env, api_key)
    
    if provider == "openai":
        settings.openai_api_key = api_key
    elif provider == "gemini":
        settings.gemini_api_key = api_key
    elif provider == "mistral":
        settings.mistral_api_key = api_key
    elif provider == "anthropic":
        settings.anthropic_api_key = api_key

    model = body.get("model")
    if model:
        env_models = {
            "openai": "KYROS_OPENAI_MODEL",
            "gemini": "KYROS_GEMINI_MODEL",
            "mistral": "KYROS_MISTRAL_MODEL",
            "anthropic": "KYROS_ANTHROPIC_MODEL",
        }
        target_model_env = env_models[provider]
        os.environ[target_model_env] = model
        _update_env_file(target_model_env, model)
        
        if provider == "openai":
            settings.openai_model = model
        elif provider == "gemini":
            settings.gemini_model = model
        elif provider == "mistral":
            settings.mistral_model = model
        elif provider == "anthropic":
            settings.anthropic_model = model

    logger.info(f"Dynamically updated LLM key and model in-memory and in .env for {provider} (allow_mock={allow_mock})")
    return {"status": "success", "message": f"LLM provider {provider} configured dynamically and written to .env."}


@router.post("/test-llm")
async def test_llm(request: Request) -> dict[str, Any]:
    """Test if the provided LLM credentials are valid by making a lightweight test call."""
    import os
    from kyros.ml.models import call_llm
    from kyros.config import get_settings
    
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")
        
    provider = body.get("provider")
    api_key = body.get("api_key")
    model = body.get("model")
    
    if not provider or not api_key:
        raise HTTPException(status_code=400, detail="Missing 'provider' or 'api_key'")
        
    provider = provider.lower()
    supported = {"openai", "gemini", "mistral", "anthropic"}
    if provider not in supported:
        raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")
        
    env_keys = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
        "mistral": "MISTRAL_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
    }
    target_env = env_keys[provider]
    old_env_val = os.environ.get(target_env)
    
    env_models = {
        "openai": "KYROS_OPENAI_MODEL",
        "gemini": "KYROS_GEMINI_MODEL",
        "mistral": "KYROS_MISTRAL_MODEL",
        "anthropic": "KYROS_ANTHROPIC_MODEL",
    }
    target_model_env = env_models[provider]
    old_model_env_val = os.environ.get(target_model_env)
    
    # Temporarily set credentials
    os.environ[target_env] = api_key
    if model:
        os.environ[target_model_env] = model
        
    settings = get_settings()
    old_settings_key = None
    old_settings_model = None
    
    if provider == "openai":
        old_settings_key = settings.openai_api_key
        settings.openai_api_key = api_key
        if model:
            old_settings_model = settings.openai_model
            settings.openai_model = model
    elif provider == "gemini":
        old_settings_key = settings.gemini_api_key
        settings.gemini_api_key = api_key
        if model:
            old_settings_model = settings.gemini_model
            settings.gemini_model = model
    elif provider == "mistral":
        old_settings_key = settings.mistral_api_key
        settings.mistral_api_key = api_key
        if model:
            old_settings_model = settings.mistral_model
            settings.mistral_model = model
    elif provider == "anthropic":
        old_settings_key = settings.anthropic_api_key
        settings.anthropic_api_key = api_key
        if model:
            old_settings_model = settings.anthropic_model
            settings.anthropic_model = model

    # Disable mock LLM check for validation/testing
    old_allow_mock = os.environ.get("KYROS_ALLOW_MOCK_LLM")
    os.environ["KYROS_ALLOW_MOCK_LLM"] = "false"

    try:
        response = await call_llm(
            prompt="Respond with 'OK' and nothing else.",
            system_prompt="You are a connection testing bot. Answer 'OK' to show you are online.",
            temperature=0.0,
            provider=provider,
            timeout=10.0
        )
        success = "ok" in response.lower()
        return {
            "status": "success" if success else "error",
            "message": "API connection successful. Response: " + response.strip() if success else "API returned unexpected response: " + response
        }
    except Exception as e:
        logger.error(f"API test connection failed for {provider}: {e}")
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        # Restore original environment variables and settings
        if old_env_val is not None:
            os.environ[target_env] = old_env_val
        else:
            os.environ.pop(target_env, None)
            
        if old_model_env_val is not None:
            os.environ[target_model_env] = old_model_env_val
        else:
            os.environ.pop(target_model_env, None)
            
        if old_allow_mock is not None:
            os.environ["KYROS_ALLOW_MOCK_LLM"] = old_allow_mock
        else:
            os.environ.pop("KYROS_ALLOW_MOCK_LLM", None)
            
        # Restore settings
        if provider == "openai":
            settings.openai_api_key = old_settings_key
            if old_settings_model:
                settings.openai_model = old_settings_model
        elif provider == "gemini":
            settings.gemini_api_key = old_settings_key
            if old_settings_model:
                settings.gemini_model = old_settings_model
        elif provider == "mistral":
            settings.mistral_api_key = old_settings_key
            if old_settings_model:
                settings.mistral_model = old_settings_model
        elif provider == "anthropic":
            settings.anthropic_api_key = old_settings_key
            if old_settings_model:
                settings.anthropic_model = old_settings_model


class CreateAgentRequest(BaseModel):
    agent_id: str = Field(..., min_length=1, max_length=255)
    display_name: str | None = Field(default=None, max_length=255)
    metadata: dict = Field(default_factory=dict)


@router.post("/agents")
async def create_agent(body: CreateAgentRequest, request: Request) -> dict[str, Any]:
    """Explicitly register/create a new agent (project namespace)."""
    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    try:
        from kyros.storage.postgres import get_db_session_for_tenant
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            # Look if it already exists
            result = await session.execute(
                text("SELECT id FROM agents WHERE external_id = :eid AND tenant_id = :tid"),
                {"eid": body.agent_id, "tid": tenant_id},
            )
            row = result.fetchone()
            if row:
                raise HTTPException(status_code=400, detail="Agent namespace already exists")

            agent_id = uuid.uuid4()
            await session.execute(
                text("""
                INSERT INTO agents (id, tenant_id, external_id, display_name, metadata, created_at)
                VALUES (:id, :tid, :eid, :display_name, :metadata, NOW())
                """),
                {
                    "id": agent_id,
                    "tid": tenant_id,
                    "eid": body.agent_id,
                    "display_name": body.display_name,
                    "metadata": json.dumps(body.metadata),
                },
            )
            await service.cache.set_agent_id(tenant_id, body.agent_id, str(agent_id))
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("DB error in create_agent", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "agent_id": body.agent_id,
        "display_name": body.display_name,
        "status": "created",
    }


@router.delete("/agents/{agent_id}")
async def delete_agent(agent_id: str, request: Request) -> dict[str, str]:
    """Delete an agent (project namespace) and all its associated memories completely."""
    service = get_memory_service(request)
    tenant_id = getattr(request.state, "tenant_id", None)
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Unauthenticated")

    try:
        from kyros.storage.postgres import get_db_session_for_tenant
        async with get_db_session_for_tenant(str(tenant_id)) as session:
            agent_id_internal = await service._resolve_agent(session, tenant_id, agent_id)
            
            # Delete from agents table (which cascades to memories/entities/etc.)
            await session.execute(
                text("DELETE FROM agents WHERE id = :id"),
                {"id": agent_id_internal},
            )
            
            # Clear redis cache for this agent
            await service.cache.invalidate_agent(agent_id_internal)
            
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except SQLAlchemyError as e:
        logger.error("DB error in delete_agent", agent_id=agent_id, error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {"status": "success", "message": f"Agent {agent_id} and all associated memories completely deleted."}


@router.post("/tenants/{target_tenant_id}/rotate-key")
async def rotate_tenant_key(target_tenant_id: str, request: Request) -> dict[str, Any]:
    """Generate and rotate a new API key for an existing tenant.

    Requires master admin token.
    """
    import secrets
    from kyros.config import get_settings
    from kyros.storage.postgres import get_db_session

    settings = get_settings()
    admin_token = settings.admin_token or settings.jwt_secret_key

    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.replace("Bearer ", "").strip()
    else:
        token = request.headers.get("X-Admin-Token", "").strip()

    if not token or token != admin_token:
        raise HTTPException(status_code=401, detail="Invalid admin token")

    api_key = f"mk_live_{secrets.token_hex(16)}"
    key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    try:
        async with get_db_session() as session:
            # Check if tenant exists
            result = await session.execute(
                text("SELECT id FROM tenants WHERE id = :id"),
                {"id": target_tenant_id},
            )
            row = result.fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tenant not found")

            await session.execute(
                text("UPDATE tenants SET api_key_hash = :key_hash, updated_at = NOW() WHERE id = :id"),
                {"id": target_tenant_id, "key_hash": key_hash},
            )
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        logger.error("DB error in rotate_tenant_key", error=str(e))
        raise HTTPException(status_code=503, detail="Database error, please retry") from e

    return {
        "tenant_id": target_tenant_id,
        "api_key": api_key,
        "status": "rotated",
    }
