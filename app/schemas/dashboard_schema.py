"""Dashboard CRUD schemas."""

from __future__ import annotations

import datetime as dt
from typing import Any

from pydantic import BaseModel, ConfigDict


class WidgetConfig(BaseModel):
    chart_type: str
    chart_config: dict[str, Any] = {}
    query_id: int | None = None
    title: str | None = None
    position_x: int = 0
    position_y: int = 0
    width: int = 6
    height: int = 4


class DashboardCreate(BaseModel):
    title: str
    description: str | None = None


class DashboardUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    is_public: bool | None = None


class WidgetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    chart_type: str
    chart_config_json: dict[str, Any] | None = None
    query_id: int | None = None
    title: str | None = None
    position_x: int
    position_y: int
    width: int
    height: int


class DashboardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    is_public: bool
    widgets: list[WidgetResponse] = []
    created_at: dt.datetime
    updated_at: dt.datetime | None = None


class DashboardListResponse(BaseModel):
    dashboards: list[DashboardResponse]
    total: int
