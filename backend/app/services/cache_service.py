"""
Redis cache abstraction.

Provides a thin async wrapper around redis-py so other services can
cache / invalidate data without coupling to the Redis client directly.
Connection failures are logged but never crash the application.
"""

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Async Redis cache with graceful degradation."""

    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    async def _get_client(self) -> aioredis.Redis:
        """Lazily initialize and return the Redis client."""
        if self._redis is None:
            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                decode_responses=True,
            )
        return self._redis

    @property
    def client(self) -> aioredis.Redis | None:
        """Sync accessor for modules that need the raw client (best-effort)."""
        return self._redis

    async def get_client(self) -> aioredis.Redis:
        """Async accessor used by WebSocket Pub/Sub and judge queue."""
        return await self._get_client()

    async def get(self, key: str) -> str | None:
        """Fetch a value by key; returns None on miss or connection error."""
        try:
            client = await self._get_client()
            return await client.get(key)
        except Exception:
            logger.warning("Redis GET failed for key=%s", key, exc_info=True)
            return None

    async def get_json(self, key: str) -> Any | None:
        """Fetch and deserialize a JSON value."""
        raw = await self.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    async def set(
        self,
        key: str,
        value: str,
        ttl: int = 300,
    ) -> None:
        """Store a value with an expiration in seconds."""
        try:
            client = await self._get_client()
            await client.setex(key, ttl, value)
        except Exception:
            logger.warning("Redis SET failed for key=%s", key, exc_info=True)

    async def set_json(self, key: str, value: Any, ttl: int = 300) -> None:
        """Serialize *value* to JSON and store it."""
        await self.set(key, json.dumps(value, default=str), ttl)

    async def delete(self, key: str) -> None:
        """Remove a single key."""
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception:
            logger.warning("Redis DEL failed for key=%s", key, exc_info=True)

    async def delete_pattern(self, pattern: str) -> None:
        """Remove all keys matching a glob pattern (e.g. ``problems:*``)."""
        try:
            client = await self._get_client()
            cursor = 0
            while True:
                cursor, keys = await client.scan(cursor, match=pattern, count=100)
                if keys:
                    await client.delete(*keys)
                if cursor == 0:
                    break
        except Exception:
            logger.warning("Redis DEL pattern failed for %s", pattern, exc_info=True)

    async def lpush(self, key: str, value: str) -> None:
        """Push a value onto the left of a Redis list."""
        try:
            client = await self._get_client()
            await client.lpush(key, value)
        except Exception:
            logger.warning("Redis LPUSH failed for key=%s", key, exc_info=True)

    async def brpop(self, key: str, timeout: int = 5) -> str | None:
        """Blocking pop from the right of a Redis list."""
        try:
            client = await self._get_client()
            result = await client.brpop(key, timeout=timeout)
            if result:
                return result[1]
            return None
        except Exception:
            logger.warning("Redis BRPOP failed for key=%s", key, exc_info=True)
            return None

    async def publish(self, channel: str, message: str) -> None:
        """Publish a message to a Redis Pub/Sub channel."""
        try:
            client = await self._get_client()
            await client.publish(channel, message)
        except Exception:
            logger.warning("Redis PUBLISH failed for channel=%s", channel, exc_info=True)

    async def incr_with_ttl(self, key: str, ttl: int) -> int:
        """Increment a counter and set TTL on first increment."""
        try:
            client = await self._get_client()
            count = await client.incr(key)
            if count == 1:
                await client.expire(key, ttl)
            return int(count)
        except Exception:
            logger.warning("Redis INCR failed for key=%s", key, exc_info=True)
            return 0

    async def zadd(self, key: str, mapping: dict[str, float]) -> None:
        """Add members to a sorted set."""
        try:
            client = await self._get_client()
            await client.zadd(key, mapping)
        except Exception:
            logger.warning("Redis ZADD failed for key=%s", key, exc_info=True)

    async def zrevrange(self, key: str, start: int, end: int) -> list[str]:
        """Return sorted set members in descending score order."""
        try:
            client = await self._get_client()
            return await client.zrevrange(key, start, end, withscores=False)
        except Exception:
            logger.warning("Redis ZREVRANGE failed for key=%s", key, exc_info=True)
            return []

    async def zrevrange_with_scores(
        self, key: str, start: int, end: int
    ) -> list[tuple[str, float]]:
        """Return sorted set members with scores."""
        try:
            client = await self._get_client()
            return await client.zrevrange(key, start, end, withscores=True)
        except Exception:
            logger.warning("Redis ZREVRANGE failed for key=%s", key, exc_info=True)
            return []

    async def close(self) -> None:
        """Shut down the Redis connection pool."""
        if self._redis is not None:
            await self._redis.close()
            self._redis = None


cache_service = CacheService()
