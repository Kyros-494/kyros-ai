"""Redis cache for hot memory access patterns."""

from __future__ import annotations

import json
from uuid import UUID

import redis.asyncio as redis


async def get_redis(url: str) -> redis.Redis:
    """Create and return an async Redis connection."""
    return redis.from_url(url, decode_responses=True)


async def close_redis(client: redis.Redis) -> None:
    """Close Redis connection."""
    await client.close()


class MemoryCache:
    """Redis cache for hot memory access patterns."""

    EPISODIC_RECENT = "ep:{agent_id}:recent"
    SEMANTIC_HOT = "sem:{agent_id}:hot"
    AGENT_SUMMARY = "agent:{agent_id}:summary"
    # Maps external_id → internal UUID per tenant (avoids DB lookup on every op)
    AGENT_ID = "agent_id:{tenant_id}:{external_id}"

    EPISODIC_TTL = 3600
    SEMANTIC_TTL = 86400
    SUMMARY_TTL = 1800
    AGENT_ID_TTL = 3600  # 1 hour — agent IDs are stable

    def __init__(self, redis_client: redis.Redis) -> None:
        self.redis = redis_client

    async def get_agent_id(self, tenant_id: UUID, external_id: str) -> str | None:
        """Return the cached internal agent UUID for a given external_id, or None."""
        key = self.AGENT_ID.format(tenant_id=tenant_id, external_id=external_id)
        return await self.redis.get(key)

    async def set_agent_id(self, tenant_id: UUID, external_id: str, agent_uuid: str) -> None:
        """Cache the external_id → internal UUID mapping."""
        key = self.AGENT_ID.format(tenant_id=tenant_id, external_id=external_id)
        await self.redis.set(key, agent_uuid, ex=self.AGENT_ID_TTL)

    async def cache_episodic_memory(
        self, agent_id: UUID, memory_id: str, content: str, timestamp: float
    ) -> None:
        """Add to recent memories sorted set, keep only last 100."""
        key = self.EPISODIC_RECENT.format(agent_id=agent_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.zadd(key, {json.dumps({"id": memory_id, "content": content[:500]}): timestamp})
            pipe.zremrangebyrank(key, 0, -101)
            pipe.expire(key, self.EPISODIC_TTL)
            await pipe.execute()

    async def get_recent_episodic(self, agent_id: UUID, limit: int = 20) -> list[dict]:
        """Get most recent episodic memories from cache."""
        key = self.EPISODIC_RECENT.format(agent_id=agent_id)
        results = await self.redis.zrevrange(key, 0, limit - 1)
        return [json.loads(r) for r in results]

    async def cache_semantic_fact(
        self, agent_id: UUID, subject: str, predicate: str, value: str
    ) -> None:
        """Cache a semantic fact for fast lookup."""
        key = self.SEMANTIC_HOT.format(agent_id=agent_id)
        async with self.redis.pipeline(transaction=True) as pipe:
            pipe.hset(key, f"{subject}:{predicate}", value)
            pipe.expire(key, self.SEMANTIC_TTL)
            await pipe.execute()

    async def invalidate_agent(self, agent_id: UUID) -> None:
        """Invalidate all caches for an agent."""
        keys = [
            self.EPISODIC_RECENT.format(agent_id=agent_id),
            self.SEMANTIC_HOT.format(agent_id=agent_id),
            self.AGENT_SUMMARY.format(agent_id=agent_id),
        ]
        await self.redis.delete(*keys)
