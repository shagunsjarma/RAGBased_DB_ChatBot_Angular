"""Performance benchmark script for measuring latency of agents and DB queries."""

from __future__ import annotations

import asyncio
import os
import sys
import time

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings
from app.services.sql_service import SQLService


async def benchmark_db_query(sql_svc: SQLService, sql: str) -> float:
    """Benchmark SQL execution latency and return time in milliseconds."""
    start = time.perf_counter()
    try:
        await sql_svc.execute_query(sql)
        return (time.perf_counter() - start) * 1000
    except Exception as e:
        print(f"Query benchmark failed: {e}")
        return -1.0


async def main() -> None:
    settings = get_settings()
    print("=" * 60)
    print("MySQL Database Query Performance Benchmarking")
    print("=" * 60)

    db_engine = create_async_engine(settings.DATABASE_URL)
    sql_svc = SQLService(engine=db_engine)

    queries = [
        ("Simple Select", "SELECT 1"),
        ("Get Tables", "SHOW TABLES"),
    ]

    for label, sql in queries:
        print(f"Benchmarking {label!r}: {sql}")
        latencies = []
        for i in range(5):
            elapsed = await benchmark_db_query(sql_svc, sql)
            if elapsed > 0:
                latencies.append(elapsed)
            await asyncio.sleep(0.1)

        if latencies:
            avg_lat = sum(latencies) / len(latencies)
            min_lat = min(latencies)
            max_lat = max(latencies)
            print(f"  Avg: {avg_lat:.2f}ms | Min: {min_lat:.2f}ms | Max: {max_lat:.2f}ms\n")
        else:
            print("  Benchmark failed for all iterations.\n")

    await db_engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
