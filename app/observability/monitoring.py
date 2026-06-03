"""Health monitoring for all dependencies."""

from __future__ import annotations

import time


class HealthMonitor:
    def __init__(self, db_engine=None, redis_client=None, qdrant_client=None, llm_service=None):
        self._db = db_engine
        self._redis = redis_client
        self._qdrant = qdrant_client
        self._llm = llm_service

    async def check_health(self) -> dict:
        checks = {}
        checks["mysql"] = await self._check_mysql()
        checks["redis"] = await self._check_redis()
        checks["qdrant"] = await self._check_qdrant()
        checks["gemini"] = await self._check_gemini()

        all_up = all(c["status"] == "healthy" for c in checks.values())
        any_down = any(c["status"] == "unhealthy" for c in checks.values())
        status = "healthy" if all_up else ("unhealthy" if any_down else "degraded")
        return {"status": status, "checks": checks}

    async def _check_mysql(self) -> dict:
        if not self._db:
            return {"status": "unconfigured", "latency_ms": 0}
        try:
            from sqlalchemy import text
            start = time.perf_counter()
            async with self._db.connect() as conn:
                await conn.execute(text("SELECT 1"))
            return {"status": "healthy", "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_redis(self) -> dict:
        if not self._redis:
            return {"status": "unconfigured", "latency_ms": 0}
        try:
            start = time.perf_counter()
            ok = await self._redis.health_check()
            return {"status": "healthy" if ok else "unhealthy",
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_qdrant(self) -> dict:
        if not self._qdrant:
            return {"status": "unconfigured", "latency_ms": 0}
        try:
            start = time.perf_counter()
            ok = await self._qdrant.health_check()
            return {"status": "healthy" if ok else "unhealthy",
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}

    async def _check_gemini(self) -> dict:
        if not self._llm:
            return {"status": "unconfigured", "latency_ms": 0}
        try:
            start = time.perf_counter()
            ok = await self._llm.health_check()
            return {"status": "healthy" if ok else "unhealthy",
                    "latency_ms": round((time.perf_counter() - start) * 1000, 1)}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
