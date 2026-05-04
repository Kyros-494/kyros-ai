"""Application settings — loaded strictly from environment variables.

All fields are required unless a default is provided. The application
will refuse to start if any required variable is missing.
"""

from __future__ import annotations

import sys
from functools import lru_cache

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Kyros configuration. All values must be provided via environment or .env."""

    # ── App ──────────────────────────────────────────────────────────────
    app_name: str = Field(default="kyros")
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    log_level: str = Field(default="INFO")

    # ── Database ─────────────────────────────────────────────────────────
    database_url: str = Field(..., description="PostgreSQL async DSN (asyncpg)")
    # Pool size: 10–100 per worker. Total connections = pool_size + max_overflow.
    # For production with 4 workers: pool_size=10, max_overflow=20 → max 120 connections.
    db_pool_size: int = Field(default=10, ge=1, le=100)
    db_max_overflow: int = Field(default=20, ge=0, le=50)

    # ── Redis ────────────────────────────────────────────────────────────
    redis_url: str = Field(..., description="Redis connection URL")

    # ── Auth ─────────────────────────────────────────────────────────────
    jwt_secret_key: str = Field(
        ..., min_length=32, description="HS256 signing secret — must be ≥32 chars"
    )
    jwt_algorithm: str = Field(default="HS256")
    jwt_expiry_minutes: int = Field(default=60, ge=1)
    # How long to cache auth lookups in Redis (seconds). Revoked keys take this long to propagate.
    auth_cache_ttl: int = Field(default=300, ge=0, le=3600)

    # ── Embeddings ───────────────────────────────────────────────────────
    embedding_model: str = Field(default="all-MiniLM-L6-v2")
    embedding_dimension: int = Field(default=384, ge=1)
    # Optional secondary embedding model for cross-model portability (F01/F02).
    # When set, every memory write also populates embedding_secondary.
    # Example: KYROS_SECONDARY_EMBEDDING_MODEL=text-embedding-3-small
    secondary_embedding_model: str = Field(
        default="", description="Optional second embedding model name"
    )

    # ── Stripe (optional — only required for billing) ────────────────────
    stripe_api_key: str = Field(default="")
    stripe_webhook_secret: str = Field(default="")

    # ── Compression LLM (optional) ───────────────────────────────────────
    compression_llm_provider: str = Field(default="extractive")
    compression_llm_api_key: str = Field(default="")
    compression_llm_model: str = Field(default="")

    # ── LLM model names (configurable per-provider) ───────────────────────
    openai_model: str = Field(default="gpt-4o")
    anthropic_model: str = Field(default="claude-3-5-sonnet-20241022")
    gemini_model: str = Field(default="gemini-1.5-flash")

    # ── CORS (optional) ──────────────────────────────────────────────────
    # Comma-separated list of allowed origins. Use "*" to allow all (dev only).
    allowed_origins: str = Field(default="*", description="Comma-separated CORS origins")

    # ── Support contact (shown in error messages) ─────────────────────────
    support_email: str = Field(default="support@example.com")

    model_config = {
        "env_file": ".env",
        "env_prefix": "KYROS_",
        "extra": "ignore",  # silently ignore unknown env vars
    }

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        allowed = {"development", "staging", "production", "test"}
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}, got {v!r}")
        return v

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        allowed = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        upper = v.upper()
        if upper not in allowed:
            raise ValueError(f"log_level must be one of {allowed}, got {v!r}")
        return upper

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v.startswith(("postgresql+asyncpg://", "postgresql://", "postgres://")):
            raise ValueError(
                "database_url must be a PostgreSQL DSN starting with "
                "'postgresql+asyncpg://' or 'postgresql://'"
            )
        return v

    @model_validator(mode="after")
    def validate_production_safety(self) -> Settings:
        """Enforce stricter defaults when running in production."""
        if self.environment != "production":
            return self

        if self.debug:
            raise ValueError("debug must be false in production")

        if self.allowed_origins.strip() == "*":
            raise ValueError("allowed_origins cannot be '*' in production")

        weak_secret_markers = ("change-me", "example", "test-secret", "dev")
        secret_lower = self.jwt_secret_key.lower()
        if any(marker in secret_lower for marker in weak_secret_markers):
            raise ValueError(
                "jwt_secret_key appears to be a placeholder; set a strong production secret"
            )

        return self


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return the cached settings singleton.

    Raises a clear error on startup if any required variable is missing,
    rather than failing silently at the first DB call.
    """
    try:
        return Settings()
    except Exception as e:
        print(f"[FATAL] Configuration error: {e}", file=sys.stderr)
        print(
            "[FATAL] Copy .env.example to .env and fill in the required values.",
            file=sys.stderr,
        )
        sys.exit(1)
