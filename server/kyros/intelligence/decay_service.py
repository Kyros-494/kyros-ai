"""B06–B13 — Ebbinghaus Decay Engine: Service Layer.

B06: Auto-categorisation at write time
B07: Background freshness updater
B08: Freshness-weighted hybrid recall
B09: Freshness fields in recall response
B10: Stale memory detection
B11: Staleness report endpoint
B12: Webhook for going_stale events
B13: Re-verification workflow (flag stale, require confirmation)
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from kyros.intelligence.decay import (
    DecayConfig,
    evaluate_freshness,
)
from kyros.storage.postgres import get_db_session
from sqlalchemy import text
from kyros.logging import get_logger

logger = get_logger("kyros.decay.service")


# ─── B06: Auto-Categorisation at Write Time ───

# Keyword patterns mapped to memory categories
_CATEGORY_PATTERNS: list[tuple[list[str], str]] = [
    # Semantic categories
    (["price", "cost", "$", "€", "pricing", "rate", "fee"], "product_pricing"),
    (["stock", "market", "trade", "exchange", "forex", "index"], "market_data"),
    (["email", "phone", "address", "name is", "born", "age"], "user_identity"),
    (["prefer", "like", "want", "love", "hate", "favorite", "colour", "color"], "user_preference"),
    (["company", "org", "team", "manager", "report", "department", "ceo", "cto"], "company_structure"),
    (["regulation", "law", "compliance", "gdpr", "hipaa", "soc2", "legal"], "regulatory_rule"),
    (["api", "endpoint", "sdk", "library", "version", "deprecated"], "technical_spec"),

    # Procedural categories
    (["step", "first", "then", "next", "finally", "how to", "install", "deploy"], "workflow"),
    (["run", "execute", "command", "curl", "docker", "build"], "deployment"),
    (["error", "bug", "fix", "debug", "traceback", "exception"], "troubleshooting"),
    (["api call", "request", "response", "http", "post", "get"], "api_usage"),

    # Episodic categories
    (["meeting", "standup", "sync", "retro", "review"], "meeting"),
    (["decided", "agreed", "voted", "approved", "rejected"], "decision"),
    (["saw", "noticed", "observed", "found", "discovered"], "observation"),
]


def auto_categorise(content: str, default: str = "general") -> str:
    """Classify memory content into a decay category.

    Uses fast keyword matching (no LLM needed). Returns the category
    with the most keyword matches, or the default if no strong signal.

    Args:
        content: The memory content text.
        default: Fallback category if no pattern matches.

    Returns:
        Category string (e.g., "user_preference", "market_data").
    """
    content_lower = content.lower()
    best_category = default
    best_score = 0

    for keywords, category in _CATEGORY_PATTERNS:
        score = sum(1 for kw in keywords if kw in content_lower)
        if score > best_score:
            best_score = score
            best_category = category

    # Require at least 2 keyword hits for non-default classification
    if best_score < 2:
        return default

    return best_category


# ─── B07: Background Freshness Updater ─────────

async def update_all_freshness_scores(
    tenant_id: UUID | None = None,
    config: DecayConfig | None = None,
) -> dict:
    """Background job: recalculate freshness for all active memories atomically.

    Uses a single UPDATE per table with the decay formula computed in SQL,
    eliminating the read-modify-write race condition.

    Returns:
        Stats dict with counts of fresh/warning/critical/stale memories.
    """
    if config is None:
        config = DecayConfig()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    stats = {"fresh": 0, "warning": 0, "critical": 0, "stale": 0, "total": 0}

    tables = ["episodic_memories", "semantic_memories", "procedural_memories"]

    for table in tables:
        async with get_db_session() as session:
            tenant_filter = "AND tenant_id = :tid" if tenant_id else ""
            params: dict[str, Any] = {"now": now}
            if tenant_id:
                params["tid"] = tenant_id

            # Atomic UPDATE: compute new freshness in SQL to avoid race conditions.
            # Only update rows where the score has changed by more than 0.001.
            await session.execute(
                text(f"""
                UPDATE {table}
                SET freshness_score = GREATEST(
                    0.0,
                    LEAST(1.0, EXP(-decay_rate * EXTRACT(EPOCH FROM (:now - created_at)) / 86400.0))
                )
                WHERE deleted_at IS NULL
                  {tenant_filter}
                  AND ABS(
                    freshness_score - GREATEST(
                        0.0,
                        LEAST(1.0, EXP(-decay_rate * EXTRACT(EPOCH FROM (:now - created_at)) / 86400.0))
                    )
                  ) > 0.001
                """),
                params,
            )

            # Fetch updated stats for reporting (read-only, no race risk)
            result = await session.execute(
                text(f"""
                SELECT created_at, decay_rate, memory_category, freshness_score
                FROM {table}
                WHERE deleted_at IS NULL {tenant_filter}
                """),
                {k: v for k, v in params.items() if k != "now"},
            )
            for row in result.fetchall():
                result_eval = evaluate_freshness(
                    created_at=row.created_at,
                    category=row.memory_category or "general",
                    config=config,
                    now=now,
                )
                stats[result_eval.status] += 1
                stats["total"] += 1

    logger.info(
        "Freshness update complete",
        total=stats["total"],
        fresh=stats["fresh"],
        warning=stats["warning"],
        critical=stats["critical"],
        stale=stats["stale"],
    )

    return stats


# ─── B10: Stale Memory Detection ──────────────

async def get_stale_memories(
    agent_id: UUID,
    threshold: float = 0.40,
    limit: int = 100,
) -> list[dict]:
    """Find memories approaching staleness for a specific agent.

    Args:
        agent_id: The agent to check.
        threshold: Freshness threshold (memories below this are "stale").
        limit: Maximum results.

    Returns:
        List of stale memory dicts with id, content, freshness, category.
    """
    stale_memories = []

    tables = [
        ("episodic_memories", "episodic"),
        ("semantic_memories", "semantic"),
        ("procedural_memories", "procedural"),
    ]

    for table, mem_type in tables:
        async with get_db_session() as session:
            result = await session.execute(
                text(f"""
                SELECT id, content, freshness_score, memory_category,
                       decay_rate, created_at
                FROM {table}
                WHERE agent_id = :aid
                  AND deleted_at IS NULL
                  AND freshness_score < :threshold
                ORDER BY freshness_score ASC
                LIMIT :lim
                """),
                {"aid": agent_id, "threshold": threshold, "lim": limit},
            )
            rows = result.fetchall()

            for row in rows:
                # Determine status
                if row.freshness_score < 0.05:
                    status = "stale"
                elif row.freshness_score < 0.15:
                    status = "critical"
                else:
                    status = "warning"

                content_preview = row.content
                if hasattr(row, "content"):
                    content_preview = row.content[:200]
                elif hasattr(row, "name"):
                    content_preview = row.name

                stale_memories.append({
                    "memory_id": str(row.id),
                    "memory_type": mem_type,
                    "content_preview": content_preview,
                    "freshness_score": round(row.freshness_score, 4),
                    "category": row.memory_category or "general",
                    "decay_rate": row.decay_rate,
                    "status": status,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "half_life_days": round(math.log(2) / row.decay_rate, 1) if row.decay_rate > 0 else None,
                })

    # Sort all results by freshness (most stale first)
    stale_memories.sort(key=lambda m: m["freshness_score"])
    return stale_memories[:limit]


# ─── B11: Staleness Report ────────────────────

async def generate_staleness_report(
    agent_id: UUID,
    config: DecayConfig | None = None,
) -> dict:
    """Generate a comprehensive staleness report for an agent.

    Returns summary stats and the list of stale memories
    that need attention.
    """
    if config is None:
        config = DecayConfig()

    stale_40 = await get_stale_memories(agent_id, threshold=0.40, limit=200)
    stale_15 = [m for m in stale_40 if m["freshness_score"] < 0.15]
    stale_05 = [m for m in stale_40 if m["freshness_score"] < 0.05]

    # Group by category
    by_category: dict[str, int] = {}
    for mem in stale_40:
        cat = mem["category"]
        by_category[cat] = by_category.get(cat, 0) + 1

    return {
        "agent_id": str(agent_id),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "summary": {
            "warning_count": len(stale_40) - len(stale_15),
            "critical_count": len(stale_15) - len(stale_05),
            "stale_count": len(stale_05),
            "total_flagged": len(stale_40),
        },
        "by_category": by_category,
        "stale_memories": stale_40,
        "recommendations": _generate_recommendations(stale_40, by_category),
    }


def _generate_recommendations(stale: list[dict], by_category: dict[str, int]) -> list[str]:
    """Generate human-readable recommendations based on staleness patterns."""
    recs = []
    if not stale:
        recs.append("All memories are fresh. No action needed.")
        return recs

    total = len(stale)
    recs.append(f"{total} memories are approaching or past staleness thresholds.")

    # Identify worst categories
    if "market_data" in by_category:
        recs.append(
            f"⚠️  {by_category['market_data']} market data memories are stale. "
            f"Market data decays quickly (half-life: 1.4 days). Consider refreshing."
        )
    if "product_pricing" in by_category:
        recs.append(
            f"⚠️  {by_category['product_pricing']} pricing memories are stale. "
            f"Verify current pricing before agent uses outdated information."
        )
    if "user_preference" in by_category:
        recs.append(
            f"ℹ️  {by_category['user_preference']} user preference memories may be outdated. "
            f"Consider prompting users to confirm their preferences."
        )

    critical = sum(1 for m in stale if m["status"] == "critical")
    if critical > 0:
        recs.append(
            f"🚨 {critical} memories are in CRITICAL freshness state. "
            f"These should be re-verified or archived immediately."
        )

    return recs


# ─── B12: Webhook Events for Staleness ─────────

async def check_and_emit_staleness_webhooks(
    agent_id: UUID,
    webhook_url: str | None = None,
    config: DecayConfig | None = None,
) -> list[dict]:
    """Check for newly stale memories and emit webhook events.

    Called by the hourly scheduler. Finds memories that just crossed
    the warning threshold and sends webhook notifications.

    Returns:
        List of webhook events that were emitted.
    """
    if config is None:
        config = DecayConfig()

    stale = await get_stale_memories(agent_id, threshold=config.freshness_warning_threshold)
    events = []

    for mem in stale:
        event = {
            "event": "memory.going_stale",
            "agent_id": str(agent_id),
            "memory_id": mem["memory_id"],
            "memory_type": mem["memory_type"],
            "freshness_score": mem["freshness_score"],
            "category": mem["category"],
            "status": mem["status"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        events.append(event)

        # Send webhook if URL configured
        if webhook_url:
            try:
                import httpx
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(webhook_url, json=event)
                    logger.debug("Staleness webhook sent", memory_id=mem["memory_id"])
            except Exception as e:
                logger.warning("Webhook failed", error=str(e), url=webhook_url)

    if events:
        logger.info(
            "Staleness webhooks emitted",
            agent_id=str(agent_id),
            count=len(events),
        )

    return events


# ─── B13: Re-verification Workflow ─────────────

async def flag_stale_for_reverification(
    agent_id: UUID,
    threshold: float = 0.15,
) -> int:
    """Flag critically stale memories as needing re-verification.

    Sets a 'needs_reverification' flag in the metadata of memories
    whose freshness has dropped below the critical threshold.
    Flagged memories will include freshness_warning=true in recall.

    Returns:
        Number of memories flagged.
    """
    flagged = 0
    tables = ["episodic_memories", "semantic_memories", "procedural_memories"]

    # This is a background/admin operation — uses non-tenant session since
    # agent_id is always scoped in the WHERE clause.
    for table in tables:
        async with get_db_session() as session:
            result = await session.execute(
                text(f"""
                UPDATE {table}
                SET metadata = COALESCE(metadata, '{{}}'::jsonb) || '{{"needs_reverification": true}}'::jsonb
                WHERE agent_id = :aid
                  AND deleted_at IS NULL
                  AND freshness_score < :threshold
                  AND NOT COALESCE((metadata->>'needs_reverification')::boolean, false)
                RETURNING id
                """),
                {"aid": agent_id, "threshold": threshold},
            )
            rows = result.fetchall()
            flagged += len(rows)

    if flagged > 0:
        logger.info(
            "Flagged for reverification",
            agent_id=str(agent_id),
            count=flagged,
        )

    return flagged
