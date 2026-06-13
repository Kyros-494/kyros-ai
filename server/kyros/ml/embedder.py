"""Embedding model wrapper. Loaded once at startup, shared across requests."""

from __future__ import annotations

from kyros.logging import get_logger

logger = get_logger("kyros.ml.embedder")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class EmbeddingError(Exception):
    """Raised when embedding fails."""


class EmbeddingModel:
    """Manages the embedding model lifecycle.

    Optionally loads a secondary model for cross-model portability (F01/F02).
    When secondary_model_name is set, embed() also returns a secondary vector
    via embed_with_secondary().
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L12-v2",
        secondary_model_name: str = "",
    ) -> None:
        self._model_cache = {}
        if SentenceTransformer is None:
            raise EmbeddingError(
                "sentence-transformers is not installed. Run: pip install sentence-transformers"
            )
        try:
            self.model = SentenceTransformer(model_name)
            self.model_name = model_name
            self.dimension = self.model.get_embedding_dimension()
            self._model_cache[model_name] = self.model
            logger.info(
                "Embedding model loaded",
                model=model_name,
                dimension=self.dimension,
            )
        except Exception as e:
            raise EmbeddingError(f"Failed to load embedding model '{model_name}': {e}") from e

        # Secondary model — optional, loaded only when configured
        self.secondary_model = None
        self.secondary_model_name = ""
        self.secondary_dimension = 0

        if secondary_model_name:
            try:
                self.secondary_model = SentenceTransformer(secondary_model_name)
                self.secondary_model_name = secondary_model_name
                self.secondary_dimension = self.secondary_model.get_embedding_dimension()
                self._model_cache[secondary_model_name] = self.secondary_model
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

    def embed(self, text: str, model_name: str | None = None) -> list[float]:
        """Embed a single text string. Returns a normalized vector.

        Supports dynamic model routing:
        - openai/text-embedding-3-small, openai/text-embedding-3-large
        - gemini/text-embedding-004
        - sentence-transformers models loaded dynamically and cached
        """
        if not text or not text.strip():
            raise EmbeddingError("Cannot embed empty text")

        target_model = model_name or self.model_name

        try:
            if len(text) > 8192:
                logger.debug("Text truncated for embedding", original_len=len(text))
                text = text[:8192]

            # 1. OpenAI Integration
            if "openai" in target_model or "ada" in target_model or "embedding-3" in target_model:
                import os
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    raise EmbeddingError("OPENAI_API_KEY is not set in environment")
                clean_name = target_model.replace("openai/", "")
                if clean_name not in ("text-embedding-3-small", "text-embedding-3-large", "text-embedding-ada-002"):
                    clean_name = "text-embedding-3-small"
                client = OpenAI(api_key=api_key)
                resp = client.embeddings.create(input=[text], model=clean_name)
                return resp.data[0].embedding

            # 2. Gemini Integration
            elif "gemini" in target_model or "text-embedding-004" in target_model:
                import os
                import google.generativeai as genai
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    raise EmbeddingError("GEMINI_API_KEY is not set in environment")
                genai.configure(api_key=api_key)
                clean_name = target_model.replace("gemini/", "")
                if not clean_name.startswith("models/"):
                    clean_name = f"models/{clean_name}"
                if clean_name not in ("models/text-embedding-004", "models/embedding-001"):
                    clean_name = "models/text-embedding-004"
                result = genai.embed_content(model=clean_name, content=text)
                return result["embedding"]

            # 3. Default: SentenceTransformers (local)
            else:
                if target_model not in self._model_cache:
                    if SentenceTransformer is None:
                        raise EmbeddingError("sentence-transformers is not installed")
                    self._model_cache[target_model] = SentenceTransformer(target_model)
                model = self._model_cache[target_model]
                vec = model.encode(text, normalize_embeddings=True).tolist()
                return vec

        except Exception as e:
            logger.error("Embedding failed", error=str(e), text_preview=text[:50])
            raise EmbeddingError(f"Embedding failed: {e}") from e

    def embed_with_secondary(self, text: str, model_name: str | None = None) -> tuple[list[float], list[float] | None]:
        """Embed text with both primary and secondary models.

        Returns:
            (primary_vector, secondary_vector) — secondary is None if no secondary model loaded.
            primary_vector is truncated to 384 dimensions for schema compatibility.
        """
        primary = self.embed(text, model_name=model_name)
        
        # If the resulting embedding has 1536 dimensions (e.g. OpenAI),
        # return the first 384 elements for the primary embedding column
        # and store the full 1536-dimensional vector in the secondary column.
        if len(primary) == 1536:
            return primary[:384], primary

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
