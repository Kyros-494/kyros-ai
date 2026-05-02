"""Quick connection check before running benchmarks."""
import os, asyncio

os.environ.setdefault("KYROS_DATABASE_URL", "postgresql+asyncpg://kyros:kyros_dev_password@localhost:5433/kyros")
os.environ.setdefault("KYROS_REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("KYROS_JWT_SECRET_KEY", "dev-secret-change-in-production-kyros-2026")
os.environ.setdefault("KYROS_ENVIRONMENT", "development")
os.environ.setdefault("KYROS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
os.environ.setdefault("KYROS_EMBEDDING_DIMENSION", "384")
os.environ.setdefault("KYROS_DB_POOL_SIZE", "3")
os.environ.setdefault("KYROS_DB_MAX_OVERFLOW", "3")

async def check():
    from kyros.storage.postgres import get_db_session
    from kyros.storage.redis_cache import get_redis, close_redis
    from sqlalchemy import text

    print("Checking PostgreSQL (localhost:5433)...")
    async with get_db_session() as s:
        r = await s.execute(text("SELECT COUNT(*) FROM tenants"))
        print(f"  OK — tenants: {r.scalar()}")
        r2 = await s.execute(text("SELECT version_num FROM alembic_version"))
        print(f"  Migration version: {r2.scalar()}")

    print("Checking Redis (localhost:6379)...")
    redis = await get_redis("redis://localhost:6379/0")
    print(f"  OK — {await redis.ping()}")
    await close_redis(redis)

    print("Loading embedding model...")
    from kyros.ml.embedder import EmbeddingModel
    em = EmbeddingModel("all-MiniLM-L6-v2")
    vec = em.embed("test")
    print(f"  OK — dim={len(vec)}")

    print("\nAll connections OK. Ready to run benchmarks.")
    print("Run:  .\\benchmark.ps1 quick")

asyncio.run(check())
