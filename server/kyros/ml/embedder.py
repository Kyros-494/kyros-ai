"""Embedding model wrapper. Loaded once at startup, shared across requests."""

from __future__ import annotations

from kyros.logging import get_logger

logger = get_logger("kyros.ml.embedder")


class EmbeddingError(Exception):
    """Raised when embedding fails."""


class EmbeddingModel:
    """Manages the sentence-transformer embedding model lifecycle.

    Optionally loads a secondary model for cross-model portability (F01/F02).
    When secondary_model_name is set, embed() also returns a secondary vector
    via embed_with_secondary().
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        secondary_model_name: str = "",
    ) -> None:
        try:
            from sentence_transformers import SentenceTransformer

            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.dimension = self.model.get_sentence_embedding_dimension()
            logger.info(
                "Embedding model loaded",
                model=model_name,
                dimension=self.dimension,
            )
        except ImportError as e:
            raise EmbeddingError(
                "sentence-transformers is not installed. Run: pip install sentence-transformers"
            ) from e
        except Exception as e:
            raise EmbeddingError(f"Failed to load embedding model '{model_name}': {e}") from e

        # Secondary model — optional, loaded only when configured
        self.secondary_model = None
        self.secondary_model_name = ""
        self.secondary_dimension = 0

        if secondary_model_name:
            try:
                from sentence_transformers import SentenceTransformer

                self.secondary_model = SentenceTransformer(secondary_model_name)
                self.secondary_model_name = secondary_model_name
                self.secondary_dimension = self.secondary_model.get_sentence_embedding_dimension()
                logger.info(
                    "Secondary embedding model loaded",
                    model=secondary_model_name,
                    dimension=self.secondary_dimension,
                )
            except Exception as e:
                # Secondary model failure is non-fatal — log and continue without it
                logger.warning(
                    "Failed to load secondary embedding model — secondary embeddings disabled",
                    model=secondary_model_name,
                    error=str(e),
                )

    def embed(self, text: str) -> list[float]:
        """Embed a single text string with the primary model. Returns a normalized vector."""
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        try:
            if len(text) > 8192:
                logger.debug("Text truncated for embedding", original_len=len(text))
                text = text[:8192]
            return self.model.encode(text, normalize_embeddings=True).tolist()
        except Exception as e:
            logger.error("Embedding failed", error=str(e), text_preview=text[:50])
            raise EmbeddingError(f"Embedding failed: {e}") from e

    def embed_with_secondary(self, text: str) -> tuple[list[float], list[float] | None]:
        """Embed text with both primary and secondary models.

        Returns:
            (primary_vector, secondary_vector) — secondary is None if no secondary model loaded.
        """
        primary = self.embed(text)
        if self.secondary_model is None:
            return primary, None

        try:
            if len(text) > 8192:
                text = text[:8192]
            secondary = self.secondary_model.encode(text, normalize_embeddings=True).tolist()
            return primary, secondary
        except Exception as e:
            logger.warning("Secondary embedding failed — storing NULL", error=str(e))
            return primary, None

    def embed_batch(self, texts: list[str], batch_size: int = 64) -> list[list[float]]:
        """Embed a batch of texts with the primary model."""
        if not texts:
            raise EmbeddingError("Cannot embed an empty batch")

        sanitized = [t.strip() if t and t.strip() else " " for t in texts]

        try:
            embeddings = self.model.encode(
                sanitized, batch_size=batch_size, normalize_embeddings=True
            )
            return embeddings.tolist()
        except Exception as e:
            logger.error("Batch embedding failed", error=str(e), batch_size=len(texts))
            raise EmbeddingError(f"Batch embedding failed: {e}") from e
