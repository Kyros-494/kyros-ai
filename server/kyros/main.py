"""Kyros FastAPI application entrypoint."""

from __future__ import annotations

import asyncio
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kyros.config import get_settings
from kyros.logging import setup_logging, get_logger
from kyros.api.v1 import episodic, semantic, procedural, search, admin, causal, trust
from kyros.storage.postgres import engine, run_migrations
from kyros.storage.redis_cache import get_redis, close_redis
from kyros.ml.embedder import EmbeddingModel, EmbeddingError
from kyros.middleware.auth import AuthMiddleware
from kyros.middleware.usage_tracking import UsageTrackingMiddleware

settings = get_settings()

setup_logging(log_level=settings.log_level, environment=settings.environment)
logger = get_logger("kyros.main")

# Global set of background tasks — tracked so we can cancel them on shutdown
_background_tasks: set[asyncio.Task] = set()


def create_background_task(coro) -> asyncio.Task:
    """Create a tracked background task with exception logging.

    All fire-and-forget tasks should use this instead of asyncio.create_task()
    directly so they are properly cancelled on shutdown and exceptions are logged.
    """
    task = asyncio.create_task(coro)
    _background_tasks.add(task)

    def _on_done(t: asyncio.Task) -> None:
        _background_tasks.discard(t)
        if not t.cancelled() and t.exception() is not None:
            logger.error(
                "Background task failed",
                task=t.get_name(),
                error=str(t.exception()),
            )

    task.add_done_callback(_on_done)
    return task


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: load ML models, connect to stores. Shutdown: cleanup."""
    logger.info("Starting Kyros", environment=settings.environment, version="0.1.0")

    try:
        app.state.embedder = EmbeddingModel(
            settings.embedding_model,
            secondary_model_name=settings.secondary_embedding_model,
        )
        logger.info(
            "Embedding model loaded",
            model=settings.embedding_model,
            dim=app.state.embedder.dimension,
            secondary=settings.secondary_embedding_model or "none",
        )
    except EmbeddingError as e:
        logger.error("Failed to load embedding model — server cannot start", error=str(e))
        raise

    try:
        app.state.redis = await get_redis(settings.redis_url)
        await app.state.redis.ping()
        logger.info("Redis connected")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise

    if settings.environment in ("development", "test"):
        try:
            await run_migrations()
        except Exception as e:
            logger.warning("Migration check skipped (non-fatal in dev)", error=str(e))

    logger.info("Kyros ready")
    yield

    # ── Graceful shutdown ──────────────────────────────────────────────────
    logger.info("Shutting down Kyros...")

    # Cancel and await all pending background tasks
    if _background_tasks:
        logger.info("Waiting for background tasks", count=len(_background_tasks))
        pending = list(_background_tasks)
        for task in pending:
            task.cancel()
        results = await asyncio.gather(*pending, return_exceptions=True)
        for r in results:
            if isinstance(r, Exception) and not isinstance(r, asyncio.CancelledError):
                logger.warning("Background task error during shutdown", error=str(r))
        logger.info("Background tasks cancelled")

    try:
        await close_redis(app.state.redis)
        logger.info("Redis disconnected")
    except Exception as e:
        logger.warning("Redis close error during shutdown", error=str(e))

    try:
        await engine.dispose()
        logger.info("DB pool disposed")
    except Exception as e:
        logger.warning("Engine dispose error during shutdown", error=str(e))

    logger.info("Kyros shutdown complete")


# ─── CORS origins ─────────────────────────────
_raw_origins = getattr(settings, "allowed_origins", "*")
_cors_origins: list[str] | str = (
    [o.strip() for o in _raw_origins.split(",") if o.strip()]
    if _raw_origins != "*"
    else ["*"]
)

app = FastAPI(
    title="Kyros API",
    description="Persistent memory operating system for AI agents",
    version="0.1.0",
    docs_url="/docs" if settings.environment != "production" else None,
    redoc_url="/redoc" if settings.environment != "production" else None,
    lifespan=lifespan,
)


# ─── Global exception handlers ─────────────────

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    logger.warning("Validation error", path=request.url.path, error=str(exc))
    return JSONResponse(status_code=400, content={"error": "bad_request", "message": str(exc)})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "Unhandled exception",
        path=request.url.path,
        method=request.method,
        error=type(exc).__name__,
        detail=str(exc),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": "An unexpected error occurred"},
    )


# ─── Middleware ────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # allow_credentials requires explicit origins — cannot be used with wildcard "*"
    allow_credentials=_cors_origins != ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(UsageTrackingMiddleware)
app.add_middleware(AuthMiddleware)


# ─── Request ID ───────────────────────────────
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Apply baseline response hardening headers."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["X-XSS-Protection"] = "0"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.environment == "production":
        response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains; preload"
    return response


# ─── Request ID ───────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Attach a unique X-Request-ID to every request for distributed tracing."""
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ─── Routes ────────────────────────────────────
app.include_router(episodic.router,   prefix="/v1/memory/episodic",   tags=["Episodic Memory"])
app.include_router(semantic.router,   prefix="/v1/memory/semantic",   tags=["Semantic Memory"])
app.include_router(procedural.router, prefix="/v1/memory/procedural", tags=["Procedural Memory"])
app.include_router(search.router,     prefix="/v1/search",            tags=["Search"])
app.include_router(admin.router,      prefix="/v1/admin",             tags=["Admin"])
app.include_router(causal.router,     prefix="/v1/memory/causal",     tags=["Causal Memory"])
app.include_router(trust.router,      prefix="/v1/trust",             tags=["Trust"])


# ─── Health Checks ─────────────────────────────

@app.get("/health", tags=["System"])
async def health_check():
    """Liveness probe — returns OK if the process is running."""
    return {"status": "ok", "version": "0.1.0", "environment": settings.environment}


@app.get("/health/ready", tags=["System"])
async def readiness_check(request: Request):
    """Readiness probe — checks all dependencies before accepting traffic."""
    checks: dict[str, str] = {}
    healthy = True

    try:
        from kyros.storage.postgres import get_db_session
        from sqlalchemy import text
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as e:
        checks["postgres"] = f"error: {type(e).__name__}"
        healthy = False

    try:
        redis = getattr(request.app.state, "redis", None)
        if redis:
            await redis.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "not_initialized"
            healthy = False
    except Exception as e:
        checks["redis"] = f"error: {type(e).__name__}"
        healthy = False

    embedder = getattr(request.app.state, "embedder", None)
    checks["embedder"] = "ok" if embedder else "not_initialized"
    if not embedder:
        healthy = False

    return JSONResponse(
        status_code=200 if healthy else 503,
        content={"status": "ready" if healthy else "not_ready", "checks": checks},
    )
