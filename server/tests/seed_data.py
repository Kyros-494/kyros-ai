"""Seed script — populates all database tables with representative data.

Run inside Docker:
    docker-compose exec kyros-server python tests/seed_data.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uuid

from sqlalchemy import text

from kyros.config import get_settings
from kyros.ml.embedder import EmbeddingModel
from kyros.schemas.memory import (
    OutcomeRequest,
    RememberRequest,
    StoreFactRequest,
    StoreProcedureRequest,
)
from kyros.services.memory_service import MemoryService
from kyros.storage.postgres import get_db_session
from kyros.storage.redis_cache import MemoryCache, close_redis, get_redis


async def get_or_create_tenant(name: str) -> uuid.UUID:
    async with get_db_session() as session:
        r = await session.execute(
            text("SELECT id FROM tenants WHERE name = :name LIMIT 1"),
            {"name": name},
        )
        row = r.fetchone()
        if row:
            return row.id

    tenant_id = uuid.uuid4()
    async with get_db_session() as session:
        await session.execute(
            text("""
            INSERT INTO tenants (
                id, name, email, api_key_hash, plan, is_active, created_at, updated_at
            )
            VALUES (:id, :name, :email, :hash, 'free', true, NOW(), NOW())
            ON CONFLICT DO NOTHING
            """),
            {
                "id": tenant_id,
                "name": name,
                "email": f"seed_{tenant_id.hex[:8]}@kyros.dev",
                "hash": f"seed_{tenant_id.hex}",
            },
        )
    return tenant_id


async def seed_all() -> None:
    settings = get_settings()
    redis = await get_redis(settings.redis_url)
    embedder = EmbeddingModel(settings.embedding_model)
    cache = MemoryCache(redis)
    service = MemoryService(embedder, cache)

    tenant_id = await get_or_create_tenant("Seed Tenant")
    agent = "seed-agent"
    print(f"Using tenant: {tenant_id}, agent: {agent}")

    # ── Semantic facts (triggers semantic_edges via background indexing) ──
    print("\n[1/4] Storing semantic facts...")
    facts = [
        ("Alice", "works_at", "TechCorp"),
        ("Alice", "has_role", "Senior Engineer"),
        ("Alice", "works_in", "AI Team"),
        ("Bob", "works_at", "TechCorp"),
        ("Bob", "has_role", "Product Manager"),
        ("TechCorp", "industry", "Technology"),
        ("TechCorp", "founded", "2018"),
        ("project_alpha", "language", "Python"),
        ("project_alpha", "status", "active"),
    ]
    for subj, pred, obj in facts:
        req = StoreFactRequest(
            agent_id=agent, subject=subj, predicate=pred, object=obj, confidence=0.9
        )
        f = await service.store_fact(tenant_id, req)
        print(f"  {subj} {pred} {obj}  ->  {f.fact_id}")

    # Wait for background index_fact_relationships tasks to complete
    print("  Waiting for semantic edge indexing...")
    await asyncio.sleep(4)

    # ── Procedural memories with outcomes ────────────────────────────────
    print("\n[2/4] Storing procedures and outcomes...")
    procs = [
        (
            "Deploy to Production",
            "Steps to deploy the application to AWS ECS production environment",
            "devops",
            [
                {"action": "run_tests"},
                {"action": "build_docker"},
                {"action": "push_ecr"},
                {"action": "update_ecs"},
            ],
        ),
        (
            "Send Transactional Email",
            "Compose and send a transactional email to a user via SMTP",
            "email",
            [{"action": "get_recipient"}, {"action": "compose_body"}, {"action": "send_via_smtp"}],
        ),
        (
            "Parse CSV File",
            "Read a CSV file and extract structured data rows with validation",
            "data_processing",
            [{"action": "open_file"}, {"action": "read_rows"}, {"action": "validate_schema"}],
        ),
        (
            "Backup Database",
            "Create a full PostgreSQL backup and upload to S3 cold storage",
            "devops",
            [{"action": "pg_dump"}, {"action": "compress"}, {"action": "s3_upload"}],
        ),
        (
            "Onboard New User",
            "Create account, send welcome email, and provision default resources",
            "user_management",
            [
                {"action": "create_account"},
                {"action": "send_welcome"},
                {"action": "provision_resources"},
            ],
        ),
    ]
    proc_ids = []
    for name, desc, task_type, steps in procs:
        req = StoreProcedureRequest(
            agent_id=agent, name=name, description=desc, task_type=task_type, steps=steps
        )
        p = await service.store_procedure(tenant_id, req)
        proc_ids.append(p.procedure_id)
        print(f"  {name}  ->  {p.procedure_id}")

    # Report outcomes to populate success_count / failure_count
    for i, pid in enumerate(proc_ids):
        successes = 5 - i  # first proc has most successes
        for _ in range(successes):
            await service.report_outcome(
                tenant_id,
                OutcomeRequest(procedure_id=pid, success=True, duration_ms=100.0 + i * 20),
            )
        if i > 0:
            await service.report_outcome(tenant_id, OutcomeRequest(procedure_id=pid, success=False))
    print("  Outcomes reported.")

    # ── Episodic memories with explicit causal links ──────────────────────
    print("\n[3/4] Storing episodic memories with causal links...")
    mem1 = await service.remember_episodic(
        tenant_id,
        RememberRequest(
            agent_id=agent,
            content=(
                "User reported the deployment pipeline was failing due to "
                "missing KYROS_DATABASE_URL env var"
            ),
            importance=0.9,
        ),
    )
    mem2 = await service.remember_episodic(
        tenant_id,
        RememberRequest(
            agent_id=agent,
            content="Team fixed the deployment by adding KYROS_DATABASE_URL to the CI/CD config",
            importance=0.8,
            cause_memory_id=str(mem1.memory_id),
        ),
    )
    mem3 = await service.remember_episodic(
        tenant_id,
        RememberRequest(
            agent_id=agent,
            content="Deployment succeeded after the env var fix — all health checks passed",
            importance=0.7,
            cause_memory_id=str(mem2.memory_id),
        ),
    )
    print(f"  Causal chain: {mem1.memory_id} -> {mem2.memory_id} -> {mem3.memory_id}")

    # A few more episodic memories for variety
    memories = [
        ("User prefers dark mode in all applications", 0.6),
        ("User is allergic to peanuts — critical dietary restriction", 0.95),
        ("Meeting scheduled for Monday at 10am with the design team", 0.7),
        ("Budget approved for cloud infrastructure: $5,000/month", 0.8),
        ("User's preferred programming language is Python for backend work", 0.75),
    ]
    for content, importance in memories:
        await service.remember_episodic(
            tenant_id,
            RememberRequest(agent_id=agent, content=content, importance=importance),
        )
    print(f"  Stored {len(memories)} additional episodic memories.")

    # Wait for background Merkle + causal tasks
    print("\n[4/4] Waiting for background tasks (Merkle, causal edges)...")
    await asyncio.sleep(3)

    await close_redis(redis)

    # ── Final counts ──────────────────────────────────────────────────────
    print("\n── Final table counts ──────────────────────────────────────")
    async with get_db_session() as session:
        tables = [
            "tenants",
            "agents",
            "episodic_memories",
            "semantic_memories",
            "procedural_memories",
            "causal_edges",
            "semantic_edges",
            "memory_audit_logs",
            "usage_events",
            "semantic_propagation_logs",
        ]
        for tbl in tables:
            r = await session.execute(text(f"SELECT COUNT(*) FROM {tbl}"))
            count = r.scalar()
            status = "✅" if count and count > 0 else "⚠️  empty"
            print(f"  {tbl:<30} {count:>6}  {status}")

    print("\nSeeding complete.")


if __name__ == "__main__":
    asyncio.run(seed_all())
