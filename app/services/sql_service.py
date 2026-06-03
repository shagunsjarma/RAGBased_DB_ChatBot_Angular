"""SQL service – query execution against MySQL."""

from __future__ import annotations

import asyncio
import time

from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from app.core.constants import MAX_RESULT_ROWS, MAX_SQL_EXECUTION_TIME
from app.schemas.sql_schema import QueryExecutionResult
from app.core.logger import get_logger

logger = get_logger(__name__)


class SQLService:
    def __init__(self, engine: AsyncEngine) -> None:
        self._engine = engine

    async def execute_query(self, sql: str, timeout: int = MAX_SQL_EXECUTION_TIME) -> QueryExecutionResult:
        """Execute a read-only SQL query and return structured results."""
        start = time.perf_counter()
        try:
            async with self._engine.connect() as conn:
                result = await asyncio.wait_for(
                    conn.execute(text(sql)), timeout=timeout,
                )
                column_names = list(result.keys())
                raw_rows = result.fetchall()

                truncated = len(raw_rows) > MAX_RESULT_ROWS
                if truncated:
                    raw_rows = raw_rows[:MAX_RESULT_ROWS]

                rows = [dict(zip(column_names, row)) for row in raw_rows]
                elapsed = round((time.perf_counter() - start) * 1000, 2)

                logger.info("sql_executed", rows=len(rows), time_ms=elapsed)
                return QueryExecutionResult(
                    columns=column_names, rows=rows,
                    row_count=len(rows), execution_time_ms=elapsed,
                    truncated=truncated,
                )
        except asyncio.TimeoutError:
            raise TimeoutError(f"Query timed out after {timeout}s")

    async def get_schema_info(self) -> dict:
        """Return database schema: tables and their columns."""
        async with self._engine.connect() as conn:
            table_names = await conn.run_sync(
                lambda c: inspect(c).get_table_names()
            )
            schema = {}
            for table in table_names:
                cols = await conn.run_sync(
                    lambda c, t=table: inspect(c).get_columns(t)
                )
                schema[table] = [
                    {"name": c["name"], "type": str(c["type"]), "nullable": c.get("nullable", True)}
                    for c in cols
                ]
        return schema

    async def explain_query(self, sql: str) -> str:
        """Run EXPLAIN on the SQL and return formatted output."""
        async with self._engine.connect() as conn:
            result = await conn.execute(text(f"EXPLAIN {sql}"))
            rows = result.fetchall()
            cols = list(result.keys())
            lines = [" | ".join(cols)]
            lines.append("-" * len(lines[0]))
            for row in rows:
                lines.append(" | ".join(str(v) for v in row))
            return "\n".join(lines)
