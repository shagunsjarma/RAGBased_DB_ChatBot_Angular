"""Dashboard repository – dashboards & widgets CRUD."""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.dashboard_model import Dashboard, DashboardWidget


class DashboardRepository:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_dashboard(self, user_id: int, title: str, description: str | None = None) -> Dashboard:
        db = Dashboard(user_id=user_id, title=title, description=description)
        self._session.add(db)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(db)
        return db

    async def get_dashboard(self, dashboard_id: int, user_id: int | None = None) -> Dashboard | None:
        stmt = select(Dashboard).options(selectinload(Dashboard.widgets)).where(Dashboard.id == dashboard_id)
        if user_id is not None:
            stmt = stmt.where(Dashboard.user_id == user_id)
        return await self._session.scalar(stmt)

    async def list_dashboards(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Dashboard], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(Dashboard).where(Dashboard.user_id == user_id)
        ) or 0
        result = await self._session.execute(
            select(Dashboard).options(selectinload(Dashboard.widgets))
            .where(Dashboard.user_id == user_id).order_by(Dashboard.updated_at.desc())
            .offset(skip).limit(limit)
        )
        return list(result.scalars().unique().all()), total

    async def update_dashboard(self, dashboard_id: int, **kwargs: Any) -> Dashboard | None:
        db = await self.get_dashboard(dashboard_id)
        if db is None:
            return None
        for k, v in kwargs.items():
            if hasattr(db, k):
                setattr(db, k, v)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(db)
        return db

    async def delete_dashboard(self, dashboard_id: int, user_id: int) -> bool:
        await self._session.execute(delete(DashboardWidget).where(DashboardWidget.dashboard_id == dashboard_id))
        result = await self._session.execute(
            delete(Dashboard).where(Dashboard.id == dashboard_id, Dashboard.user_id == user_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def add_widget(self, dashboard_id: int, widget_config: dict[str, Any]) -> DashboardWidget:
        w = DashboardWidget(
            dashboard_id=dashboard_id,
            chart_type=widget_config.get("chart_type", "bar"),
            chart_config_json=widget_config.get("chart_config", {}),
            query_id=widget_config.get("query_id"),
            title=widget_config.get("title"),
            position_x=widget_config.get("position_x", 0),
            position_y=widget_config.get("position_y", 0),
            width=widget_config.get("width", 6),
            height=widget_config.get("height", 4),
        )
        self._session.add(w)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(w)
        return w

    async def update_widget(self, widget_id: int, **kwargs: Any) -> DashboardWidget | None:
        w = await self._session.scalar(select(DashboardWidget).where(DashboardWidget.id == widget_id))
        if w is None:
            return None
        for k, v in kwargs.items():
            if hasattr(w, k):
                setattr(w, k, v)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(w)
        return w

    async def delete_widget(self, widget_id: int) -> bool:
        result = await self._session.execute(delete(DashboardWidget).where(DashboardWidget.id == widget_id))
        await self._session.commit()
        return result.rowcount > 0
