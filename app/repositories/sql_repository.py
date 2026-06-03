"""SQL query-history repository."""

from __future__ import annotations

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.query_model import QueryHistory


class SQLRepository:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_query_record(self, user_id: int, nl_query: str, generated_sql: str,
                                   status: str = "success", execution_time_ms: int | None = None,
                                   row_count: int | None = None, error_message: str | None = None) -> QueryHistory:
        record = QueryHistory(user_id=user_id, nl_query=nl_query, generated_sql=generated_sql,
                              status=status, execution_time_ms=execution_time_ms,
                              row_count=row_count, error_message=error_message)
        self._session.add(record)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(record)
        return record

    async def get_query(self, query_id: int) -> QueryHistory | None:
        return await self._session.scalar(select(QueryHistory).where(QueryHistory.id == query_id))

    async def list_user_queries(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[QueryHistory], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(QueryHistory).where(QueryHistory.user_id == user_id)
        ) or 0
        result = await self._session.execute(
            select(QueryHistory).where(QueryHistory.user_id == user_id)
            .order_by(QueryHistory.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def get_similar_queries(self, user_id: int, nl_query: str, limit: int = 5) -> list[QueryHistory]:
        result = await self._session.execute(
            select(QueryHistory).where(QueryHistory.user_id == user_id, QueryHistory.status == "success")
            .order_by(QueryHistory.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    async def get_query_stats(self, user_id: int) -> dict:
        stmt = select(
            func.count().label("total"),
            func.sum(case((QueryHistory.status == "success", 1), else_=0)).label("success"),
            func.avg(QueryHistory.execution_time_ms).label("avg_time"),
        ).select_from(QueryHistory).where(QueryHistory.user_id == user_id)
        row = (await self._session.execute(stmt)).one()
        total = row.total or 0
        success = row.success or 0
        return {
            "total_queries": total, "successful_queries": success,
            "failed_queries": total - success,
            "success_rate": round(success / total, 4) if total else 0.0,
            "avg_execution_time_ms": round(float(row.avg_time), 2) if row.avg_time else None,
        }
