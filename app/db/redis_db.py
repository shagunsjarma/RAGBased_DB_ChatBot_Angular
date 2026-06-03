"""Async Redis client wrapper."""

from __future__ import annotations

import json
from typing import Any

import redis.asyncio as aioredis


class RedisClient:
    """Async Redis wrapper with JSON helpers and health checks."""

    def __init__(self, url: str | None = None) -> None:
        self._url = url
        self._client: aioredis.Redis | None = None

    async def connect(self, url: str | None = None) -> None:
        target = url or self._url
        self._client = aioredis.from_url(
            target, decode_responses=True, encoding="utf-8",
        )

    async def close(self) -> None:
        if self._client:
            await self._client.close()
            self._client = None

    @property
    def client(self) -> aioredis.Redis:
        if self._client is None:
            raise RuntimeError("RedisClient not connected.")
        return self._client

    # ── Primitives ───────────────────────────────────────────────────
    async def get(self, key: str) -> str | None:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ttl: int | None = None) -> None:
        await self.client.set(key, value, ex=ttl)

    async def delete(self, key: str) -> None:
        await self.client.delete(key)

    async def exists(self, key: str) -> bool:
        return bool(await self.client.exists(key))

    # ── JSON helpers ─────────────────────────────────────────────────
    async def get_json(self, key: str) -> dict[str, Any] | None:
        raw = await self.get(key)
        if raw is None:
            return None
        return json.loads(raw)

    async def set_json(self, key: str, data: dict[str, Any], ttl: int | None = None) -> None:
        await self.set(key, json.dumps(data, default=str), ttl=ttl)

    # ── Utilities ────────────────────────────────────────────────────
    async def flush_pattern(self, pattern: str) -> int:
        keys = []
        async for key in self.client.scan_iter(match=pattern):
            keys.append(key)
        if keys:
            await self.client.delete(*keys)
        return len(keys)

    async def increment(self, key: str) -> int:
        return await self.client.incr(key)

    async def health_check(self) -> bool:
        try:
            return await self.client.ping()
        except Exception:
            return False
