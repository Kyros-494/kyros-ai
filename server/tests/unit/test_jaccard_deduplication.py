"""Unit tests for the optimized Jaccard Hybrid Deduplication Filter."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pytest
from kyros.services.memory_service import MemoryService


class MockRow:
    """Mock database row compatible with deduplication content checks."""
    def __init__(self, id_val: str, content: str) -> None:
        self.id = id_val
        self.content = content
        self.memory_type = "episodic"
        self.hybrid_score = 1.0
        self.importance = 0.5
        self.created_at = None
        self.metadata = {}
        self.freshness_score = 1.0


class TestJaccardDeduplication:
    @pytest.fixture
    def service(self) -> MemoryService:
        """Create a MemoryService with mocked dependencies."""
        mock_embedder = MagicMock()
        mock_cache = MagicMock()
        return MemoryService(embedder=mock_embedder, cache=mock_cache)

    def test_absolute_identity_jaccard_bypass(self, service: MemoryService) -> None:
        """Identical content must be deduped instantly with Jaccard bypass of SequenceMatcher."""
        rows = [
            MockRow("id-1", "The quick brown fox jumps over the lazy dog"),
            MockRow("id-2", "The quick brown fox jumps over the lazy dog"),
        ]

        # Patch SequenceMatcher to verify it is NEVER called
        with patch("difflib.SequenceMatcher") as mock_matcher:
            deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
            
            assert len(deduped) == 1
            assert deduped[0].id == "id-1"
            mock_matcher.assert_not_called()

    def test_absolute_divergence_jaccard_bypass(self, service: MemoryService) -> None:
        """Completely different content must bypass SequenceMatcher and be preserved."""
        rows = [
            MockRow("id-1", "The quick brown fox jumps over the lazy dog"),
            MockRow("id-2", "Python programming language is extremely popular for ML"),
            MockRow("id-3", "PostgreSQL database supports vector database HNSW indexes natively"),
        ]

        with patch("difflib.SequenceMatcher") as mock_matcher:
            deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
            
            assert len(deduped) == 3
            mock_matcher.assert_not_called()

    def test_ambiguous_range_sequence_matcher_fallback(self, service: MemoryService) -> None:
        """Content in the ambiguous overlap zone [0.30, 0.85] must invoke SequenceMatcher."""
        # Jaccard overlap of these is ~0.45, triggering fallback
        rows = [
            MockRow("id-1", "Alice lives in San Francisco and studies computer science"),
            MockRow("id-2", "Alice lives in San Francisco and studies mechanical engineering"),
        ]

        with patch("difflib.SequenceMatcher") as mock_matcher:
            # Configure mock to return high similarity (> threshold)
            mock_instance = MagicMock()
            mock_instance.ratio.return_value = 0.90
            mock_matcher.return_value = mock_instance

            deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
            
            # Since similarity 0.90 > threshold 0.85, it must deduplicate
            assert len(deduped) == 1
            assert deduped[0].id == "id-1"
            mock_matcher.assert_called_once()

    def test_ambiguous_range_preserves_distinct_items(self, service: MemoryService) -> None:
        """Content in ambiguous zone but below ratio threshold must be preserved."""
        rows = [
            MockRow("id-1", "Alice lives in San Francisco and studies computer science"),
            MockRow("id-2", "Alice lives in San Francisco and studies mechanical engineering"),
        ]

        with patch("difflib.SequenceMatcher") as mock_matcher:
            # Configure mock to return low similarity (< threshold)
            mock_instance = MagicMock()
            mock_instance.ratio.return_value = 0.70
            mock_matcher.return_value = mock_instance

            deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
            
            # Since similarity 0.70 < threshold 0.85, both must be preserved
            assert len(deduped) == 2
            mock_matcher.assert_called_once()

    def test_metadata_prefix_stripping(self, service: MemoryService) -> None:
        """Metadata chat prefixes like '[user]: ' should be stripped prior to Jaccard check."""
        rows = [
            MockRow("id-1", "[user]: Hello how can I help you today?"),
            MockRow("id-2", "[agent]: Hello how can I help you today?"),
        ]

        with patch("difflib.SequenceMatcher") as mock_matcher:
            deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
            
            # Stripped versions are identical, so it must deduplicate instantly
            assert len(deduped) == 1
            assert deduped[0].id == "id-1"
            mock_matcher.assert_not_called()
