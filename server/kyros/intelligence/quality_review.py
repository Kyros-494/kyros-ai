"""E84 — Compression quality review script.

Generates 50 compression summaries for manual quality review.
Outputs a report with original memories, generated summaries,
and compression ratios for human evaluation.

Usage:
    python -m kyros.intelligence.quality_review > review_report.md
"""

from __future__ import annotations

import random
from datetime import UTC, datetime

from kyros.intelligence.compression import BATCH_SIZE_L1, CompressionEngine
from kyros.logging import get_logger

logger = get_logger("kyros.intelligence.quality_review")

NUM_REVIEWS = 50


def generate_synthetic_memories(count: int) -> list[dict]:
    """Generate synthetic memories for quality review when DB is empty."""
    templates = [
        "User asked about {topic} and I explained the key differences.",
        "Completed {action} successfully in {time}ms.",
        "User preference updated: {preference}.",
        "Error encountered during {operation}: {error}. Retried and succeeded.",
        "User mentioned they work at {company} as a {role}.",
        "Discussed {topic} — user wants to implement it next sprint.",
        "Tool call: {tool}({params}) returned {result}.",
        "User feedback: '{feedback}' — saved for future reference.",
        "Session started. User context: returning customer, {plan} plan.",
        "Scheduled follow-up for {date} regarding {topic}.",
    ]

    topics = ["machine learning", "pricing", "deployment", "API design", "database optimization"]
    actions = ["data export", "batch import", "model training", "cache refresh"]
    companies = ["Acme Corp", "TechStart", "DataFlow Inc", "CloudScale"]
    roles = ["engineer", "PM", "CTO", "data scientist"]
    tools = ["search_api", "send_email", "query_db", "generate_report"]

    memories = []
    for i in range(count):
        template = random.choice(templates)
        # Build a complete kwargs dict so every possible key is always present
        fmt_kwargs = dict(
            topic=random.choice(topics),
            action=random.choice(actions),
            time=random.randint(50, 5000),
            preference=f"prefers {random.choice(['dark mode', 'light mode', 'Python', 'TypeScript'])}",
            operation=random.choice(actions),
            error=f"timeout after {random.randint(10, 60)}s",
            company=random.choice(companies),
            role=random.choice(roles),
            tool=random.choice(tools),
            params=f"query='{random.choice(topics)}'",
            result=f"200 OK, {random.randint(1, 50)} results",
            feedback=random.choice(["Great!", "Could be faster", "Love the new feature", "Needs improvement"]),
            plan=random.choice(["free", "pro", "team"]),
            date=f"2026-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
        )
        try:
            content = template.format(**fmt_kwargs)
        except KeyError:
            content = f"Memory item {i}: synthetic test data."
        memories.append({
            "content": content,
            "importance": round(random.uniform(0.1, 1.0), 2),
            "created_at": datetime.now(UTC).isoformat(),
        })

    return memories


def run_quality_review() -> None:
    """Generate compression summaries for quality review."""
    engine = CompressionEngine()

    print("# Compression Quality Review Report")
    print(f"Generated: {datetime.now(UTC).isoformat()}")
    print(f"Backend: {engine.backend}")
    print(f"Batch size: {BATCH_SIZE_L1}")
    print(f"Reviews: {NUM_REVIEWS}")
    print()
    print("---")
    print()

    total_ratio = 0.0
    passing = 0

    for review_num in range(1, NUM_REVIEWS + 1):
        batch_size = random.randint(10, 30)
        memories = generate_synthetic_memories(batch_size)

        result = engine.compress_batch(memories, target_level=1)

        print(f"## Review #{review_num}")
        print(f"- **Input**: {batch_size} memories ({sum(len(m['content']) for m in memories)} chars)")
        print(f"- **Output**: {len(result.summary)} chars")
        print(f"- **Ratio**: {result.compression_ratio}:1")
        print(f"- **Latency**: {result.latency_ms}ms")
        print()
        print("### Sample Input (first 3):")
        for m in memories[:3]:
            print(f"  - {m['content'][:100]}...")
        print()
        print("### Summary:")
        print(f"> {result.summary}")
        print()

        # Quality checks
        checks = []
        if result.compression_ratio >= 3.0:
            checks.append("✅ Ratio ≥ 3:1")
        else:
            checks.append("⚠️ Ratio < 3:1")

        if len(result.summary) > 20:
            checks.append("✅ Non-trivial output")
        else:
            checks.append("⚠️ Output too short")

        if result.summary and not result.summary.startswith("Error"):
            checks.append("✅ No errors")
            passing += 1
        else:
            checks.append("❌ Error in output")

        print(f"### Checks: {' | '.join(checks)}")
        print()
        print("---")
        print()

        total_ratio += result.compression_ratio

    avg_ratio = total_ratio / NUM_REVIEWS if NUM_REVIEWS > 0 else 0
    print("## Summary")
    print(f"- **Average ratio**: {avg_ratio:.1f}:1")
    print(f"- **Pass rate**: {passing}/{NUM_REVIEWS} ({100*passing/NUM_REVIEWS:.0f}%)")
    print("- **Target**: 20:1 compression ratio")


if __name__ == "__main__":
    run_quality_review()
