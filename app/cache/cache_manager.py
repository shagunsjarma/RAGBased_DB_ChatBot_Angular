"""Cache manager with decorator-based caching."""

from __future__ import annotations

import functools
import hashlib
import json
from typing import Any, Callable

from app.db.redis_db import RedisClient


class CacheManager:
    def __init__(self, redis_client: RedisClient) -> None:
        self._redis = redis_client

    def cached(self, ttl: int = 300, key_prefix: str = ""):
        """Decorator to cache async function results in Redis."""
        def decorator(func: Callable):
            @functools.wraps(func)
            async def wrapper(*args, **kwargs):
                key = self._generate_cache_key(key_prefix or func.__name__, *args, **kwargs)
                cached_val = await self._redis.get_json(key)
                if cached_val is not None:
                    return cached_val
                result = await func(*args, **kwargs)
                try:
                    await self._redis.set_json(key, result if isinstance(result, dict) else {"result": result}, ttl=ttl)
                except Exception:
                    pass
                return result
            return wrapper
        return decorator

    async def get_or_set(self, key: str, factory: Callable, ttl: int = 300) -> Any:
        cached = await self._redis.get_json(key)
        if cached is not None:
            return cached
        result = await factory()
        await self._redis.set_json(key, result, ttl=ttl)
        return result

    async def invalidate_pattern(self, pattern: str) -> int:
        return await self._redis.flush_pattern(pattern)

    async def get_stats(self) -> dict:
        healthy = await self._redis.health_check()
        return {"status": "connected" if healthy else "disconnected"}

    def _generate_cache_key(self, prefix: str, *args, **kwargs) -> str:
        raw = json.dumps({"a": str(args[1:]), "k": str(kwargs)}, sort_keys=True, default=str)
        h = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"cache:{prefix}:{h}"
