"""Dashboard and DashboardWidget ORM models."""

from __future__ import annotations

from typing import Any

from sqlalchemy import Boolean, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import BaseModel


class Dashboard(BaseModel):
    __tablename__ = "dashboards"

    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships
    user = relationship("User", back_populates="dashboards")
    widgets: Mapped[list["DashboardWidget"]] = relationship(back_populates="dashboard", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Dashboard id={self.id} title={self.title!r}>"


class DashboardWidget(BaseModel):
    __tablename__ = "dashboard_widgets"

    dashboard_id: Mapped[int] = mapped_column(Integer, ForeignKey("dashboards.id"), nullable=False, index=True)
    chart_type: Mapped[str] = mapped_column(String(30), nullable=False)
    chart_config_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    query_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("query_history.id"), nullable=True)
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    position_x: Mapped[int] = mapped_column(Integer, default=0)
    position_y: Mapped[int] = mapped_column(Integer, default=0)
    width: Mapped[int] = mapped_column(Integer, default=6)
    height: Mapped[int] = mapped_column(Integer, default=4)

    # Relationships
    dashboard = relationship("Dashboard", back_populates="widgets")

    def __repr__(self) -> str:
        return f"<DashboardWidget id={self.id} type={self.chart_type!r}>"
