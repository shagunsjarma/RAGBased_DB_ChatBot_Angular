"""Dashboard service – CRUD for dashboards and widgets."""

from __future__ import annotations

from app.core.exceptions import NotFoundError
from app.repositories.dashboard_repository import DashboardRepository
from app.schemas.dashboard_schema import (
    DashboardListResponse, DashboardResponse, WidgetConfig, WidgetResponse,
)


class DashboardService:
    def __init__(self, dashboard_repo: DashboardRepository) -> None:
        self._repo = dashboard_repo

    async def create_dashboard(self, user_id: int, title: str,
                                description: str | None = None) -> DashboardResponse:
        db = await self._repo.create_dashboard(user_id, title, description)
        return DashboardResponse.model_validate(db)

    async def get_dashboard(self, dashboard_id: int, user_id: int) -> DashboardResponse:
        db = await self._repo.get_dashboard(dashboard_id, user_id=user_id)
        if not db:
            raise NotFoundError("Dashboard not found")
        return DashboardResponse.model_validate(db)

    async def list_dashboards(self, user_id: int, page: int = 1,
                               page_size: int = 20) -> DashboardListResponse:
        skip = (page - 1) * page_size
        dbs, total = await self._repo.list_dashboards(user_id, skip=skip, limit=page_size)
        return DashboardListResponse(
            dashboards=[DashboardResponse.model_validate(d) for d in dbs], total=total,
        )

    async def update_dashboard(self, dashboard_id: int, user_id: int, **kwargs) -> DashboardResponse:
        db = await self._repo.get_dashboard(dashboard_id, user_id=user_id)
        if not db:
            raise NotFoundError("Dashboard not found")
        updated = await self._repo.update_dashboard(dashboard_id, **kwargs)
        return DashboardResponse.model_validate(updated)

    async def delete_dashboard(self, dashboard_id: int, user_id: int) -> bool:
        deleted = await self._repo.delete_dashboard(dashboard_id, user_id)
        if not deleted:
            raise NotFoundError("Dashboard not found")
        return True

    async def add_widget(self, dashboard_id: int, user_id: int,
                          widget_config: WidgetConfig) -> WidgetResponse:
        db = await self._repo.get_dashboard(dashboard_id, user_id=user_id)
        if not db:
            raise NotFoundError("Dashboard not found")
        w = await self._repo.add_widget(dashboard_id, widget_config.model_dump())
        return WidgetResponse.model_validate(w)

    async def update_widget(self, widget_id: int, **kwargs) -> WidgetResponse:
        w = await self._repo.update_widget(widget_id, **kwargs)
        if not w:
            raise NotFoundError("Widget not found")
        return WidgetResponse.model_validate(w)

    async def delete_widget(self, widget_id: int) -> bool:
        deleted = await self._repo.delete_widget(widget_id)
        if not deleted:
            raise NotFoundError("Widget not found")
        return True
