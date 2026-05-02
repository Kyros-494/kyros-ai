"""Unit tests for the EmbeddingModel and MemoryCache."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4


# ─── EmbeddingModel Tests ─────────────────────

class TestEmbeddingModel:

    def _make_embedder(self, dim: int = 384):
        """Helper: build an EmbeddingModel with a mocked SentenceTransformer."""
        import numpy as np
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = dim
            mock_model.encode.return_value = np.random.randn(dim).astype(np.float32)
            MockST.return_value = mock_model
            from kyros.ml.embedder import EmbeddingModel
            embedder = EmbeddingModel("test-model")
            embedder._mock_model = mock_model  # keep reference for assertions
            return embedder

    def test_embed_returns_list_of_floats(self):
        embedder = self._make_embedder(384)
        result = embedder.embed("Hello world")
        assert isinstance(result, list)
        assert len(result) == 384
        assert all(isinstance(x, float) for x in result)

    def test_embed_calls_encode_once(self):
        embedder = self._make_embedder()
        embedder.embed("test")
        embedder._mock_model.encode.assert_called_once()

    def test_embed_raises_on_empty_string(self):
        from kyros.ml.embedder import EmbeddingModel, EmbeddingError
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            MockST.return_value = mock_model
            embedder = EmbeddingModel("test-model")
            with pytest.raises(EmbeddingError, match="empty"):
                embedder.embed("")

    def test_embed_raises_on_whitespace_only(self):
        from kyros.ml.embedder import EmbeddingModel, EmbeddingError
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            MockST.return_value = mock_model
            embedder = EmbeddingModel("test-model")
            with pytest.raises(EmbeddingError, match="empty"):
                embedder.embed("   ")

    def test_embed_batch_returns_list_of_lists(self):
        import numpy as np
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.randn(3, 384).astype(np.float32)
            MockST.return_value = mock_model
            from kyros.ml.embedder import EmbeddingModel
            embedder = EmbeddingModel("test-model")
            results = embedder.embed_batch(["a", "b", "c"])
            assert len(results) == 3
            assert all(len(r) == 384 for r in results)

    def test_embed_batch_raises_on_empty_list(self):
        from kyros.ml.embedder import EmbeddingModel, EmbeddingError
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            MockST.return_value = mock_model
            embedder = EmbeddingModel("test-model")
            with pytest.raises(EmbeddingError, match="empty batch"):
                embedder.embed_batch([])

    def test_embed_batch_sanitizes_empty_strings(self):
        """Empty strings in a batch should be replaced with a space, not crash."""
        import numpy as np
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.return_value = np.random.randn(3, 384).astype(np.float32)
            MockST.return_value = mock_model
            from kyros.ml.embedder import EmbeddingModel
            embedder = EmbeddingModel("test-model")
            # Should not raise even with empty strings in the batch
            results = embedder.embed_batch(["hello", "", "world"])
            assert len(results) == 3

    def test_dimension_property(self):
        embedder = self._make_embedder(768)
        assert embedder.dimension == 768

    def test_model_load_failure_raises_embedding_error(self):
        from kyros.ml.embedder import EmbeddingError
        with patch("kyros.ml.embedder.SentenceTransformer", side_effect=RuntimeError("model not found")):
            with pytest.raises(EmbeddingError, match="Failed to load"):
                from kyros.ml.embedder import EmbeddingModel
                EmbeddingModel("nonexistent-model")

    def test_embed_model_error_raises_embedding_error(self):
        from kyros.ml.embedder import EmbeddingError
        with patch("kyros.ml.embedder.SentenceTransformer") as MockST:
            mock_model = MagicMock()
            mock_model.get_sentence_embedding_dimension.return_value = 384
            mock_model.encode.side_effect = RuntimeError("CUDA out of memory")
            MockST.return_value = mock_model
            from kyros.ml.embedder import EmbeddingModel
            embedder = EmbeddingModel("test-model")
            with pytest.raises(EmbeddingError, match="Embedding failed"):
                embedder.embed("test text")


# ─── MemoryCache Tests ────────────────────────

class TestMemoryCache:

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client with a synchronous pipeline (matches redis.asyncio behavior)."""
        redis = AsyncMock()
        pipe = MagicMock()  # pipeline() is sync in redis.asyncio
        pipe.zadd = MagicMock()
        pipe.zremrangebyrank = MagicMock()
        pipe.expire = MagicMock()
        pipe.hset = MagicMock()
        pipe.incr = MagicMock()
        pipe.execute = AsyncMock(return_value=[1, True])
        redis.pipeline.return_value = pipe
        redis.zrevrange = AsyncMock(return_value=[])
        redis.delete = AsyncMock()
        return redis

    @pytest.mark.asyncio
    async def test_cache_episodic_memory_calls_pipeline(self, mock_redis):
        """Caching an episodic memory should queue zadd + trim + expire then execute."""
        from kyros.storage.redis_cache import MemoryCache
        cache = MemoryCache(mock_redis)
        agent_id = uuid4()

        await cache.cache_episodic_memory(
            agent_id=agent_id,
            memory_id="mem-123",
            content="Test memory content",
            timestamp=1700000000.0,
        )

        pipe = mock_redis.pipeline.return_value
        pipe.zadd.assert_called_once()
        pipe.zremrangebyrank.assert_called_once()
        pipe.expire.assert_called_once()
        pipe.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_get_recent_episodic_empty_cache(self, mock_redis):
        """Getting recent memories from an empty cache should return []."""
        from kyros.storage.redis_cache import MemoryCache
        cache = MemoryCache(mock_redis)
        results = await cache.get_recent_episodic(uuid4(), limit=10)
        assert results == []

    @pytest.mark.asyncio
    async def test_cache_semantic_fact_calls_hset(self, mock_redis):
        """Caching a semantic fact should queue hset + expire then execute."""
        from kyros.storage.redis_cache import MemoryCache
        cache = MemoryCache(mock_redis)

        await cache.cache_semantic_fact(uuid4(), "user_123", "language", "Python")

        pipe = mock_redis.pipeline.return_value
        pipe.hset.assert_called_once()
        pipe.expire.assert_called_once()
        pipe.execute.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_invalidate_agent_deletes_three_keys(self, mock_redis):
        """Invalidating an agent should delete exactly 3 cache keys."""
        from kyros.storage.redis_cache import MemoryCache
        cache = MemoryCache(mock_redis)

        await cache.invalidate_agent(uuid4())

        mock_redis.delete.assert_awaited_once()
        args = mock_redis.delete.call_args[0]
        assert len(args) == 3, f"Expected 3 keys deleted, got {len(args)}"
