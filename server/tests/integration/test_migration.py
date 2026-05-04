"""F16 — Integration tests for Cross-Model Memory Portability."""


import pytest

from kyros.ml.translation import MODEL_REGISTRY, EmbeddingTranslator, benchmark_translation_accuracy


@pytest.mark.asyncio
async def test_translation_linear_produces_correct_dimension() -> None:
    """Linear projection should produce a vector of the target model's dimension."""
    translator = EmbeddingTranslator()
    source_vec = [0.1] * 384

    target_vec = translator.translate_linear(
        source_vec, "all-MiniLM-L6-v2", "text-embedding-3-small"
    )
    assert len(target_vec) == MODEL_REGISTRY["text-embedding-3-small"].dimension


@pytest.mark.asyncio
async def test_translation_mlp_produces_correct_dimension() -> None:
    """MLP projection should produce a vector of the target model's dimension."""
    translator = EmbeddingTranslator()
    source_vec = [0.1] * 384

    target_vec = translator.translate_mlp(source_vec, "all-MiniLM-L6-v2", "text-embedding-3-small")
    assert len(target_vec) == MODEL_REGISTRY["text-embedding-3-small"].dimension


@pytest.mark.asyncio
async def test_translation_unknown_source_raises() -> None:
    """Translating from an unknown model should raise ValueError."""
    translator = EmbeddingTranslator()
    with pytest.raises(ValueError, match="Unknown source model"):
        translator.translate_mlp([0.1] * 384, "unknown-model", "all-MiniLM-L6-v2")


@pytest.mark.asyncio
async def test_translation_unknown_target_raises() -> None:
    """Translating to an unknown model should raise ValueError."""
    translator = EmbeddingTranslator()
    with pytest.raises(ValueError, match="Unknown target model"):
        translator.translate_mlp([0.1] * 384, "all-MiniLM-L6-v2", "unknown-target-model")


@pytest.mark.asyncio
async def test_benchmark_translation_accuracy_returns_expected_keys() -> None:
    """Benchmark should return a dict with the required metric keys."""
    translator = EmbeddingTranslator()

    # Build a minimal paired dataset using models that exist in the registry
    dataset = [
        {
            "text_preview": "Hello world",
            "embeddings": {
                "all-MiniLM-L6-v2": [0.5] * 384,
                "models/embedding-001": [0.45] * 768,
            },
        }
    ]

    result = benchmark_translation_accuracy(
        translator, dataset, "all-MiniLM-L6-v2", "models/embedding-001", method="mlp"
    )
    assert "retrieval_accuracy_estimate_pct" in result
    assert "avg_mse_loss" in result
    assert "samples_tested" in result
    assert result["samples_tested"] == 1
    assert 0.0 <= result["retrieval_accuracy_estimate_pct"] <= 100.0


@pytest.mark.asyncio
async def test_benchmark_empty_dataset_returns_zero() -> None:
    """Benchmark with empty dataset should return zero samples and zero accuracy."""
    translator = EmbeddingTranslator()
    result = benchmark_translation_accuracy(
        translator, [], "all-MiniLM-L6-v2", "models/embedding-001"
    )
    assert result["samples_tested"] == 0
    assert result["retrieval_accuracy_estimate_pct"] == 0.0
