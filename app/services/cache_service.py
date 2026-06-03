"""Cache service – Redis-backed query result caching."""

from __future__ import annotations

import hashlib
import json

from app.db.redis_db import RedisClient
from app.core.constants import CACHE_TTL_SECONDS
from app.core.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    def __init__(self, redis_client: RedisClient) -> None:
        self._redis = redis_client

    async def get_cached_result(self, query: str) -> dict | None:
        key = self._generate_key(query)
        data = await self._redis.get_json(key)
        if data:
            logger.debug("cache_hit", key=key[:20])
        return data

    async def cache_result(self, query: str, result: dict, ttl: int = CACHE_TTL_SECONDS) -> None:
        key = self._generate_key(query)
        await self._redis.set_json(key, result, ttl=ttl)

    async def invalidate(self, pattern: str | None = None) -> int:
        if pattern:
            return await self._redis.flush_pattern(f"query_cache:{pattern}*")
        return await self._redis.flush_pattern("query_cache:*")

    async def get_cache_stats(self) -> dict:
        return {"status": "connected" if await self._redis.health_check() else "disconnected"}

    def _generate_key(self, query: str) -> str:
        normalized = " ".join(query.lower().split())
        h = hashlib.sha256(normalized.encode()).hexdigest()[:16]
        return f"query_cache:{h}"
