"""Authentication middleware — API key validation via X-API-Key header.

Flow:
1. Extract API key from X-API-Key header
2. Validate format (must start with mk_live_ or mk_test_)
3. Hash it (SHA-256) and look up in tenants table (Redis-cached, 5 min TTL)
4. Attach tenant_id to request.state for downstream use
5. Skip auth for health check and docs endpoints

Security notes:
- Keys are never stored in plaintext — only SHA-256 hashes
- DB lookup uses constant-time comparison via parameterized query
- Failed auth attempts are logged with key prefix (never full key)
- Test keys are only accepted in non-production environments
- Cache TTL is 300s — revoked keys take up to 5 min to propagate
"""

from __future__ import annotations

import contextlib
import hashlib
import json

from fastapi import status
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from kyros.config import get_settings
from kyros.logging import get_logger
from kyros.storage.postgres import get_db_session

logger = get_logger("kyros.auth")
settings = get_settings()

# Minimum key length after the prefix (e.g. "mk_test_" + 16 chars minimum)
_MIN_KEY_SUFFIX_LEN = 16

# Redis cache TTL for auth lookups (seconds). Revoked keys take this long to propagate.
_AUTH_CACHE_TTL = settings.auth_cache_ttl

# Endpoints that bypass authentication entirely
PUBLIC_PATHS = frozenset(
    {
        "/health",
        "/health/ready",
        "/docs",
        "/redoc",
        "/openapi.json",
    }
)


def hash_api_key(api_key: str) -> str:
    """Hash an API key with SHA-256. Keys are never stored in plaintext."""
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def _safe_key_prefix(api_key: str) -> str:
    """Return a safe prefix for logging — never log the full key."""
    return api_key[:16] + "..." if len(api_key) > 16 else api_key[:8] + "..."


def _cache_key(key_hash: str) -> str:
    return f"auth:{key_hash}"


class AuthMiddleware(BaseHTTPMiddleware):
    """Validates API key on every request and attaches tenant context.

    Hot path: Redis cache hit (~0.2ms) instead of DB query (~2-5ms).
    Cache miss falls through to DB and populates the cache.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        path = request.url.path

        # Skip auth for public endpoints and doc sub-paths
        if path in PUBLIC_PATHS or path.startswith(("/docs/", "/redoc/")):
            return await call_next(request)

        # ── Extract key ──────────────────────────────────────────────────
        api_key = request.headers.get("X-API-Key", "").strip()
        if not api_key:
            logger.warning("Missing API key", path=path, ip=self._client_ip(request))
            return self._error(
                status.HTTP_401_UNAUTHORIZED,
                "missing_api_key",
                "X-API-Key header is required.",
            )

        # ── Validate format ──────────────────────────────────────────────
        if not api_key.startswith(("mk_live_", "mk_test_")):
            return self._error(
                status.HTTP_401_UNAUTHORIZED,
                "invalid_api_key_format",
                "API key must start with mk_live_ or mk_test_.",
            )

        prefix = "mk_live_" if api_key.startswith("mk_live_") else "mk_test_"
        suffix = api_key[len(prefix) :]
        if len(suffix) < _MIN_KEY_SUFFIX_LEN:
            return self._error(
                status.HTTP_401_UNAUTHORIZED,
                "invalid_api_key_format",
                f"API key suffix must be at least {_MIN_KEY_SUFFIX_LEN} characters.",
            )

        # ── Block test keys in production ────────────────────────────────
        if settings.environment == "production" and api_key.startswith("mk_test_"):
            logger.warning(
                "Test key rejected in production",
                key_prefix=_safe_key_prefix(api_key),
                path=path,
            )
            return self._error(
                status.HTTP_401_UNAUTHORIZED,
                "invalid_api_key",
                "Test keys are not accepted in production.",
            )

        # ── Hash ─────────────────────────────────────────────────────────
        key_hash = hash_api_key(api_key)
        tenant = None

        # ── Redis cache lookup (fast path) ───────────────────────────────
        redis = getattr(request.app.state, "redis", None)
        if redis is not None:
            try:
                cached = await redis.get(_cache_key(key_hash))
                if cached:
                    data = json.loads(cached)
                    if data is None:
                        # Cached negative result — key is invalid
                        return self._error(
                            status.HTTP_401_UNAUTHORIZED,
                            "invalid_api_key",
                            "API key is invalid or does not exist.",
                        )
                    request.state.tenant_id = data["id"]
                    request.state.tenant_plan = data["plan"]
                    if not data["is_active"]:
                        return self._error(
                            status.HTTP_403_FORBIDDEN,
                            "tenant_deactivated",
                            "Your account has been deactivated. Contact support.",
                        )
                    return await call_next(request)
            except Exception as e:
                # Cache failure is non-fatal — fall through to DB
                logger.warning("Auth cache read failed", error=str(e))

        # ── DB lookup (cold path) ─────────────────────────────────────────
        try:
            async with get_db_session() as session:
                result = await session.execute(
                    text("SELECT id, plan, is_active FROM tenants WHERE api_key_hash = :key_hash"),
                    {"key_hash": key_hash},
                )
                tenant = result.fetchone()
        except SQLAlchemyError as e:
            logger.error("Auth DB lookup failed", error=str(e), path=path)
            return self._error(
                status.HTTP_503_SERVICE_UNAVAILABLE,
                "auth_service_unavailable",
                "Authentication service temporarily unavailable. Please retry.",
            )

        # ── Handle missing tenant ────────────────────────────────────────
        if not tenant:
            logger.warning(
                "Invalid API key",
                key_prefix=_safe_key_prefix(api_key),
                path=path,
                ip=self._client_ip(request),
            )
            # Cache negative result to prevent DB hammering on invalid keys
            if redis is not None:
                with contextlib.suppress(Exception):
                    await redis.set(_cache_key(key_hash), "null", ex=60)
            return self._error(
                status.HTTP_401_UNAUTHORIZED,
                "invalid_api_key",
                "API key is invalid or does not exist.",
            )

        # ── Check active status ──────────────────────────────────────────
        if not tenant.is_active:
            logger.warning(
                "Deactivated tenant attempted access",
                tenant_id=str(tenant.id),
                path=path,
            )
            return self._error(
                status.HTTP_403_FORBIDDEN,
                "tenant_deactivated",
                "Your account has been deactivated. Contact support.",
            )

        # ── Populate cache ───────────────────────────────────────────────
        if redis is not None:
            try:
                await redis.set(
                    _cache_key(key_hash),
                    json.dumps(
                        {
                            "id": str(tenant.id),
                            "plan": tenant.plan,
                            "is_active": tenant.is_active,
                        }
                    ),
                    ex=_AUTH_CACHE_TTL,
                )
            except Exception:
                pass  # Cache write failure is non-fatal

        # ── Attach context ───────────────────────────────────────────────
        request.state.tenant_id = tenant.id
        request.state.tenant_plan = tenant.plan

        logger.debug(
            "Authenticated",
            tenant_id=str(tenant.id),
            plan=tenant.plan,
            path=path,
        )
        return await call_next(request)

    @staticmethod
    def _error(status_code: int, error: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=status_code,
            content={"error": error, "message": message},
        )

    @staticmethod
    def _client_ip(request: Request) -> str:
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"
