"""B17 — Integration tests for the Ebbinghaus Decay Engine.

Tests the full freshness lifecycle: calculation, categorization,
batch updates, staleness detection, and decay configuration.

Usage:
    cd server && uv run pytest tests/integration/test_decay.py -v
"""

import math
from datetime import UTC, datetime, timedelta

from kyros.intelligence.decay import (
    DEFAULT_DECAY_RATES,
    DecayConfig,
    assign_decay_rate,
    batch_freshness_update,
    calculate_freshness,
    evaluate_freshness,
)
from kyros.intelligence.decay_service import auto_categorise


def _now() -> datetime:
    """Return a naive UTC datetime for use in decay calculations."""
    return datetime.now(UTC).replace(tzinfo=None)


# ─── B05: Freshness Formula ───────────────────


class TestFreshnessCalculation:
    def test_brand_new_memory_is_fully_fresh(self) -> None:
        now = _now()
        score = calculate_freshness(created_at=now, decay_rate=0.02, now=now)
        assert score == 1.0

    def test_memory_decays_over_time(self) -> None:
        now = _now()
        one_week_ago = now - timedelta(days=7)
        score = calculate_freshness(created_at=one_week_ago, decay_rate=0.02, now=now)
        assert 0.85 < score < 0.90  # Should be ~0.869

    def test_high_decay_rate_decays_fast(self) -> None:
        now = _now()
        one_day_ago = now - timedelta(days=1)
        # market_data has decay_rate=0.5, half-life ~1.4 days
        score = calculate_freshness(created_at=one_day_ago, decay_rate=0.5, now=now)
        assert score < 0.65  # Should be ~0.606

    def test_low_decay_rate_stays_fresh_long(self) -> None:
        now = _now()
        six_months_ago = now - timedelta(days=180)
        # regulatory_rule has decay_rate=0.001, half-life ~693 days
        score = calculate_freshness(created_at=six_months_ago, decay_rate=0.001, now=now)
        assert score > 0.80  # Should be ~0.835

    def test_very_old_memory_approaches_zero(self) -> None:
        now = _now()
        years_ago = now - timedelta(days=3650)
        score = calculate_freshness(created_at=years_ago, decay_rate=0.02, now=now)
        assert score < 0.001  # Essentially zero

    def test_negative_age_clamped_to_zero(self) -> None:
        now = _now()
        future = now + timedelta(days=1)
        score = calculate_freshness(created_at=future, decay_rate=0.02, now=now)
        assert score == 1.0

    def test_zero_decay_rate_never_decays(self) -> None:
        now = _now()
        old = now - timedelta(days=1000)
        score = calculate_freshness(created_at=old, decay_rate=0.0, now=now)
        assert score == 1.0


# ─── B04: Decay Config ────────────────────────


class TestDecayConfig:
    def test_default_rates_exist(self) -> None:
        assert "market_data" in DEFAULT_DECAY_RATES
        assert "user_preference" in DEFAULT_DECAY_RATES
        assert "user_identity" in DEFAULT_DECAY_RATES

    def test_custom_rate_overrides_default(self) -> None:
        config = DecayConfig(custom_rates={"market_data": 1.0})
        assert config.get_rate("market_data") == 1.0  # Overridden
        assert config.get_rate("user_preference") == 0.020  # Default

    def test_unknown_category_uses_fallback(self) -> None:
        config = DecayConfig()
        rate = config.get_rate("totally_unknown_category")
        assert rate == 0.02  # Fallback

    def test_half_life_calculation(self) -> None:
        config = DecayConfig()
        hl = config.get_half_life_days("market_data")
        expected = math.log(2) / 0.5
        assert abs(hl - expected) < 0.01


# ─── Freshness Status Classification ──────────


class TestFreshnessEvaluation:
    def test_new_memory_is_fresh(self) -> None:
        result = evaluate_freshness(
            created_at=_now(),
            category="general",
        )
        assert result.status == "fresh"
        assert result.freshness_score > 0.95

    def test_old_market_data_is_critical(self) -> None:
        result = evaluate_freshness(
            created_at=_now() - timedelta(days=5),
            category="market_data",
        )
        assert result.status in ("critical", "stale")
        assert result.freshness_score < 0.15

    def test_moderately_old_preference_is_warning(self) -> None:
        result = evaluate_freshness(
            created_at=_now() - timedelta(days=50),
            category="user_preference",
        )
        assert result.status == "warning"

    def test_identity_stays_fresh_for_months(self) -> None:
        result = evaluate_freshness(
            created_at=_now() - timedelta(days=180),
            category="user_identity",
        )
        assert result.status == "fresh"


# ─── B06: Auto-Categorisation ─────────────────


class TestAutoCategorisation:
    def test_detects_pricing(self) -> None:
        cat = auto_categorise("The product costs $49 per month with a pricing tier structure.")
        assert cat == "product_pricing"

    def test_detects_user_preference(self) -> None:
        cat = auto_categorise("The user prefers dark mode and likes Python for development.")
        assert cat == "user_preference"

    def test_detects_workflow(self) -> None:
        cat = auto_categorise("Step 1: Install Docker. Then deploy the application to production.")
        assert cat in ("workflow", "deployment")

    def test_detects_identity(self) -> None:
        cat = auto_categorise("The user's name is Alice and her email is alice@example.com.")
        assert cat == "user_identity"

    def test_falls_back_to_general(self) -> None:
        cat = auto_categorise("Today the weather was nice and we had a pleasant conversation.")
        assert cat == "general"


# ─── Decay Rate Assignment ────────────────────


class TestDecayRateAssignment:
    def test_assigns_correct_rate_for_category(self) -> None:
        rate = assign_decay_rate("market_data")
        assert rate == 0.5

    def test_assigns_fallback_for_none(self) -> None:
        rate = assign_decay_rate(None)
        assert rate == 0.02

    def test_assigns_fallback_for_unknown(self) -> None:
        rate = assign_decay_rate("unknown_category_xyz")
        assert rate == 0.02


# ─── Batch Update ─────────────────────────────


class TestBatchUpdate:
    def test_batch_updates_freshness(self) -> None:
        now = _now()
        memories = [
            {
                "id": "mem-1",
                "created_at": (now - timedelta(days=1)).isoformat(),
                "decay_rate": 0.5,
                "memory_category": "market_data",
            },
            {
                "id": "mem-2",
                "created_at": now.isoformat(),
                "decay_rate": 0.001,
                "memory_category": "user_identity",
            },
        ]

        updates = batch_freshness_update(memories, now=now)
        assert len(updates) == 2

        # Market data should be stale after 1 day
        assert updates[0]["new_freshness"] < 0.65
        assert updates[0]["should_warn"] or updates[0]["should_archive"]

        # Identity should still be fresh
        assert updates[1]["new_freshness"] > 0.99
