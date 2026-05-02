"""B04+B05 — Ebbinghaus Decay Engine.

B04: Configurable decay rate lookup table (per-category, per-tenant)
B05: Freshness score formula: base_confidence × e^(-age_days × decay_rate)

Based on Hermann Ebbinghaus's 1885 memory decay research, adapted
for AI agent memory systems. Each memory type decays at different
rates based on its domain category.

The decay equation:
    freshness = base_confidence × e^(-age_days × decay_rate)

Where:
    base_confidence = initial freshness (1.0 for new memories)
    age_days = (now - created_at).total_seconds() / 86400
    decay_rate = category-specific rate (higher = faster staleness)
"""

from __future__ import annotations

import math
from datetime import datetime, timezone
from dataclasses import dataclass, field


# ─── B04: Decay Rate Lookup Table ─────────────

# Default decay rates by memory category.
# decay_rate determines how fast freshness drops.
# half_life = ln(2) / decay_rate ≈ 0.693 / decay_rate (in days)
#
# Example: decay_rate=0.02 → half-life ~35 days (after 35 days, freshness is 50%)

DEFAULT_DECAY_RATES: dict[str, float] = {
    # ── Episodic categories ──
    "general":           0.020,   # half-life ~35 days (conversations, events)
    "conversation":      0.025,   # half-life ~28 days (chat turns)
    "observation":       0.015,   # half-life ~46 days (agent observations)
    "decision":          0.010,   # half-life ~69 days (decisions persist longer)
    "meeting":           0.020,   # half-life ~35 days (meeting notes)

    # ── Semantic categories ──
    "fact":              0.005,   # half-life ~139 days (general facts)
    "user_preference":   0.020,   # half-life ~35 days (preferences change)
    "user_identity":     0.001,   # half-life ~693 days (names, emails rarely change)
    "company_structure": 0.005,   # half-life ~139 days (org charts)
    "market_data":       0.500,   # half-life ~1.4 days (prices, rates)
    "product_pricing":   0.100,   # half-life ~7 days (pricing changes)
    "regulatory_rule":   0.001,   # half-life ~693 days (regulations are stable)
    "technical_spec":    0.010,   # half-life ~69 days (specs evolve slowly)

    # ── Procedural categories ──
    "workflow":          0.010,   # half-life ~69 days (workflows evolve)
    "api_usage":         0.050,   # half-life ~14 days (APIs change often)
    "deployment":        0.030,   # half-life ~23 days (infra changes)
    "troubleshooting":   0.020,   # half-life ~35 days (solutions may expire)
}


@dataclass
class DecayConfig:
    """Per-tenant decay rate configuration.

    Tenants can override default decay rates for specific categories.
    """

    tenant_id: str = ""
    custom_rates: dict[str, float] = field(default_factory=dict)
    freshness_warning_threshold: float = 0.40  # Alert when freshness < 40%
    freshness_critical_threshold: float = 0.15  # Critical when freshness < 15%
    auto_archive_threshold: float = 0.05        # Auto-archive when freshness < 5%

    def get_rate(self, category: str) -> float:
        """Get decay rate for a category, with tenant override support.

        Priority: tenant custom → default table → fallback 0.02
        """
        if category in self.custom_rates:
            return self.custom_rates[category]
        return DEFAULT_DECAY_RATES.get(category, 0.02)

    def get_half_life_days(self, category: str) -> float:
        """Get the half-life in days for a category.

        Half-life = ln(2) / decay_rate ≈ how many days until
        freshness drops to 50% of its initial value.
        """
        rate = self.get_rate(category)
        if rate <= 0:
            return float("inf")
        return math.log(2) / rate


# ─── B05: Freshness Score Formula ─────────────

def calculate_freshness(
    created_at: datetime,
    decay_rate: float,
    base_confidence: float = 1.0,
    now: datetime | None = None,
) -> float:
    """Calculate the current freshness score for a memory.

    Implements Ebbinghaus's forgetting curve:
        freshness = base_confidence × e^(-age_days × decay_rate)

    Args:
        created_at: When the memory was originally stored.
        decay_rate: The decay rate for this memory's category.
        base_confidence: Initial freshness value (default 1.0).
        now: Current timestamp (defaults to utcnow).

    Returns:
        Freshness score between 0.0 (completely stale) and 1.0 (fully fresh).
    """
    if now is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

    # Ensure both are naive or both are aware
    if created_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    elif created_at.tzinfo is None and now.tzinfo is not None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_seconds = max(0, (now - created_at).total_seconds())
    age_days = age_seconds / 86400.0

    freshness = base_confidence * math.exp(-age_days * decay_rate)

    # Clamp to [0.0, 1.0]
    return max(0.0, min(1.0, freshness))


@dataclass
class FreshnessResult:
    """The result of a freshness calculation."""

    freshness_score: float
    age_days: float
    decay_rate: float
    half_life_days: float
    status: str                # "fresh", "warning", "critical", "stale"
    category: str


def evaluate_freshness(
    created_at: datetime,
    category: str,
    config: DecayConfig | None = None,
    base_confidence: float = 1.0,
    now: datetime | None = None,
) -> FreshnessResult:
    """Full freshness evaluation with status classification.

    Args:
        created_at: When the memory was created.
        category: Memory category (e.g., "market_data", "user_preference").
        config: Tenant-specific decay configuration.
        base_confidence: Initial confidence/freshness value.
        now: Current time (defaults to utcnow).

    Returns:
        FreshnessResult with score, age, status, and thresholds.
    """
    if config is None:
        config = DecayConfig()

    if now is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

    decay_rate = config.get_rate(category)
    freshness = calculate_freshness(created_at, decay_rate, base_confidence, now)
    half_life = config.get_half_life_days(category)

    # Ensure timezone handling
    if created_at.tzinfo is not None and now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    elif created_at.tzinfo is None and now.tzinfo is not None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    age_days = max(0, (now - created_at).total_seconds()) / 86400.0

    # Classify status
    if freshness >= config.freshness_warning_threshold:
        status = "fresh"
    elif freshness >= config.freshness_critical_threshold:
        status = "warning"
    elif freshness >= config.auto_archive_threshold:
        status = "critical"
    else:
        status = "stale"

    return FreshnessResult(
        freshness_score=round(freshness, 6),
        age_days=round(age_days, 2),
        decay_rate=decay_rate,
        half_life_days=round(half_life, 2),
        status=status,
        category=category,
    )


def assign_decay_rate(category: str | None, config: DecayConfig | None = None) -> float:
    """Assign the correct decay rate for a memory at write time.

    Called when a new memory is stored to set its initial decay_rate.
    """
    if config is None:
        config = DecayConfig()

    return config.get_rate(category or "general")


def batch_freshness_update(
    memories: list[dict],
    config: DecayConfig | None = None,
    now: datetime | None = None,
) -> list[dict]:
    """Recalculate freshness scores for a batch of memories.

    Used by the background scheduler to periodically update
    freshness scores across all memories.

    Args:
        memories: List of memory dicts with 'created_at', 'decay_rate', 'memory_category'.
        config: Tenant-specific configuration.
        now: Current timestamp.

    Returns:
        List of dicts with 'id', 'new_freshness', 'status' for batch DB update.
    """
    if config is None:
        config = DecayConfig()
    if now is None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)

    updates = []
    for mem in memories:
        created_at = mem.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        result = evaluate_freshness(
            created_at=created_at,
            category=mem.get("memory_category", "general"),
            config=config,
            now=now,
        )

        updates.append({
            "id": mem.get("id"),
            "new_freshness": result.freshness_score,
            "status": result.status,
            "should_warn": result.status == "warning",
            "should_archive": result.status == "stale",
        })

    return updates
