"""A/B Performance Benchmarking Framework comparing legacy vs optimized memory deduplication."""

from __future__ import annotations

import time
from difflib import SequenceMatcher
from unittest.mock import MagicMock
import pytest
from kyros.services.memory_service import MemoryService


class MockRow:
    def __init__(self, content: str) -> None:
        self.content = content
        self.id = "mock-id"
        self.memory_type = "episodic"
        self.hybrid_score = 1.0
        self.importance = 0.5
        self.created_at = None
        self.metadata = {}
        self.freshness_score = 1.0


def legacy_deduplicate_rows(rows: list, max_results: int, threshold: float = 0.85) -> list:
    """The legacy N^2 * M SequenceMatcher deduplication algorithm."""
    if not rows:
        return []
    deduplicated = []
    seen_contents = []
    for row in rows:
        content = str(row.content).strip().lower()
        if "]: " in content:
            content = content.split("]: ", 1)[1]
        is_duplicate = False
        for seen in seen_contents:
            similarity = SequenceMatcher(None, content, seen).ratio()
            if similarity > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            deduplicated.append(row)
            seen_contents.append(content)
            if len(deduplicated) >= max_results:
                break
    return deduplicated


class TestABBenchmarks:
    @pytest.fixture
    def service(self) -> MemoryService:
        mock_embedder = MagicMock()
        mock_cache = MagicMock()
        return MemoryService(mock_embedder, mock_cache)

    def test_ab_deduplication_speedup(self, service: MemoryService) -> None:
        """Measure speedup of optimized Jaccard Hybrid Deduplication vs Legacy SequenceMatcher."""
        # Construct a synthetic candidate pool representing standard search results (60 items)
        distinct_content = [
            f"Candidate distinct message talking about specialized topic {i}" for i in range(40)
        ]
        identical_content = [
            "This is a highly repetitive standard turn that has been indexed multiple times"
        ] * 10
        ambiguous_content = [
            "Alice lives in San Francisco and studies computer science at the university",
            "Alice lives in San Francisco and studies computer engineering at the university",
            "Alice lives in San Francisco and studies mechanical engineering at the university",
            "Bob enjoys programming in Python and Rust for AI/ML projects",
            "Bob enjoys programming in Python and Go for AI/ML projects",
            "Bob enjoys programming in Python and C++ for AI/ML projects",
            "Deep learning models require high performance GPU instances for training",
            "Deep learning models require high performance TPU instances for training",
            "Deep learning models require high performance GPU setups for fine-tuning",
            "Database indexes like HNSW accelerate vector search in Postgres pgvector",
        ]

        synthetic_candidates = [
            MockRow(content) for content in (distinct_content + identical_content + ambiguous_content)
        ]

        iterations = 100
        max_results = 20
        threshold = 0.85

        # 1. Benchmark Legacy Deduplication
        start_legacy = time.perf_counter()
        for _ in range(iterations):
            legacy_res = legacy_deduplicate_rows(synthetic_candidates, max_results, threshold)
        end_legacy = time.perf_counter()
        legacy_duration = end_legacy - start_legacy

        # 2. Benchmark Optimized Deduplication
        start_opt = time.perf_counter()
        for _ in range(iterations):
            opt_res = service._deduplicate_rows(synthetic_candidates, max_results, threshold)
        end_opt = time.perf_counter()
        opt_duration = end_opt - start_opt

        # 3. Calculations
        speedup = legacy_duration / opt_duration
        print(f"\n[A/B BENCHMARK RESULT]")
        print(f"  - Legacy Duration ({iterations} runs): {legacy_duration:.4f}s")
        print(f"  - Optimized Duration ({iterations} runs): {opt_duration:.4f}s")
        print(f"  - Speedup Factor: {speedup:.2f}x faster")
        print(f"  - Deduplication Results Equivalence: {len(legacy_res) == len(opt_res)}")

        # Relational check: verify results are identical
        assert len(legacy_res) == len(opt_res), "Optimized output length must match legacy output"
        for i in range(len(legacy_res)):
            assert legacy_res[i].content == opt_res[i].content

        # Performance assertion: Optimized Jaccard must be at least 2.0x faster than legacy SequenceMatcher
        assert speedup >= 2.0, f"Expected speedup of >=2.0x, got {speedup:.2f}x"
