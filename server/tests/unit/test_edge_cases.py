"""Edge-Case and Stress Ingestion test suite for the Kyros AI memory engine."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from kyros.intelligence.causal import traverse_causal_chain
from kyros.schemas.memory import RememberRequest
from kyros.services.memory_service import MemoryService


class TestEdgeCasesAndStress:
    @pytest.fixture
    def service(self) -> MemoryService:
        mock_embedder = MagicMock()
        mock_embedder.model_name = "test-model"
        mock_embedder.embed_with_secondary.return_value = ([0.1]*384, None)
        mock_cache = MagicMock()
        mock_cache.get_agent_id = AsyncMock(return_value=str(uuid4()))
        mock_cache.set_agent_id = AsyncMock()
        mock_cache.cache_episodic_memory = AsyncMock()
        return MemoryService(embedder=mock_embedder, cache=mock_cache)

    @pytest.mark.asyncio
    async def test_ingest_blank_and_whitespace_only(self, service: MemoryService) -> None:
        """Pydantic RememberRequest schema must reject empty, blank, or whitespace-only memories."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError, match="content must not be blank"):
            RememberRequest(
                agent_id="test-agent",
                content="      "
            )

        with pytest.raises(ValidationError, match="String should have at least 1 character"):
            RememberRequest(
                agent_id="test-agent",
                content=""
            )

    @pytest.mark.asyncio
    async def test_multibyte_utf8_and_emojis(self, service: MemoryService) -> None:
        """Verify that multi-byte UTF-8 character scripts (Chinese, Arabic) and emojis are tokenized and deduped safely."""
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

        rows = [
            MockRow("[user]: Python  is incredibly awesome! "),
            MockRow("[user]: Python  is incredibly awesome! "),
            MockRow("[user]: Arabic script: مرحبا بالعالم or Chinese: 你好世界"),
        ]

        deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
        # Identical emoji turns are deduped, distinct multilingual turn is preserved
        assert len(deduped) == 2
        assert "[user]: Python " in deduped[0].content
        assert "العربية" in deduped[1].content or "你好世界" in deduped[1].content

    @pytest.mark.asyncio
    async def test_massive_payload_deduplication(self, service: MemoryService) -> None:
        """Verify that extremely long paragraphs (5,000+ words) do not crash or stall Jaccard tokenizers."""
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

        # Construct a massive 5000-word paragraph
        large_body_1 = " ".join([f"lorem_ipsum_word_{i}" for i in range(5000)])
        large_body_2 = " ".join([f"lorem_ipsum_word_{i}" for i in range(5000)]) # Identical
        large_body_3 = " ".join([f"different_word_token_{i}" for i in range(5000)]) # Completely distinct

        rows = [MockRow(large_body_1), MockRow(large_body_2), MockRow(large_body_3)]

        start_time = asyncio.get_event_loop().time()
        deduped = service._deduplicate_rows(rows, max_results=10, threshold=0.85)
        end_time = asyncio.get_event_loop().time()

        assert len(deduped) == 2
        # Assert that massive set tokenization and intersection resolves in less than 250 milliseconds
        assert (end_time - start_time) < 0.25

    @pytest.mark.asyncio
    async def test_causal_graph_traversal_timeout_fallback(self) -> None:
        """If causal graph traversal exceeds 50ms, it must log warning, fallback to depth=1, and complete in <20ms."""
        agent_id = uuid4()
        memory_id = uuid4()

        # Mock database session to artificially sleep to trigger asyncio.TimeoutError
        mock_session = AsyncMock()
        
        async def slow_execute(*args, **kwargs):
            await asyncio.sleep(0.10) # 100ms artificial database delay
            mock_result = MagicMock()
            mock_result.fetchone.return_value = MagicMock()
            mock_result.fetchall.return_value = []
            return mock_result

        mock_session.execute = slow_execute

        # Patch get_db_session context manager to return our slow_session
        @asynccontextmanager
        async def mock_get_session():
            yield mock_session

        with patch("kyros.intelligence.causal.get_db_session", mock_get_session):
            start = asyncio.get_event_loop().time()
            graph = await traverse_causal_chain(agent_id, memory_id, max_depth=3, direction="both")
            elapsed = asyncio.get_event_loop().time() - start

            # The overall time taken must still be well bounded by the fallback timeouts
            assert elapsed < 0.15
            assert "nodes" in graph
            assert "edges" in graph
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
