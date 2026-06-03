"""Dashboard and widgets API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status, Response
from app.core.dependencies import get_dashboard_service, get_current_user
from app.schemas.dashboard_schema import (
    DashboardCreate, DashboardUpdate, DashboardResponse, DashboardListResponse,
    WidgetConfig, WidgetResponse
)
from app.services.dashboard_service import DashboardService
from app.models.user_model import User

router = APIRouter(prefix="/dashboards", tags=["Dashboards"])


@router.post("", response_model=DashboardResponse, status_code=status.HTTP_201_CREATED)
async def create_dashboard(
    request: DashboardCreate,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Create a new dashboard for the current user."""
    return await dash_svc.create_dashboard(
        user_id=current_user.id,
        title=request.title,
        description=request.description,
    )


@router.get("", response_model=DashboardListResponse)
async def list_dashboards(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> DashboardListResponse:
    """List all dashboards created by the current user."""
    return await dash_svc.list_dashboards(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )


@router.get("/{dashboard_id}", response_model=DashboardResponse)
async def get_dashboard(
    dashboard_id: int,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Retrieve details and widgets of a specific dashboard."""
    return await dash_svc.get_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user.id,
    )


@router.put("/{dashboard_id}", response_model=DashboardResponse)
async def update_dashboard(
    dashboard_id: int,
    request: DashboardUpdate,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> DashboardResponse:
    """Update a specific dashboard's metadata."""
    update_data = request.model_dump(exclude_unset=True)
    return await dash_svc.update_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user.id,
        **update_data
    )


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_dashboard(
    dashboard_id: int,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Delete a specific dashboard."""
    await dash_svc.delete_dashboard(
        dashboard_id=dashboard_id,
        user_id=current_user.id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)



@router.post("/{dashboard_id}/widgets", response_model=WidgetResponse, status_code=status.HTTP_201_CREATED)
async def add_widget(
    dashboard_id: int,
    request: WidgetConfig,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    """Add a visualization widget to a dashboard."""
    return await dash_svc.add_widget(
        dashboard_id=dashboard_id,
        user_id=current_user.id,
        widget_config=request,
    )


@router.put("/{dashboard_id}/widgets/{widget_id}", response_model=WidgetResponse)
async def update_widget(
    dashboard_id: int,
    widget_id: int,
    request: WidgetConfig,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> WidgetResponse:
    """Update layout or chart configuration of a specific widget."""
    # Ensure ownership check
    await dash_svc.get_dashboard(dashboard_id=dashboard_id, user_id=current_user.id)
    return await dash_svc.update_widget(
        widget_id=widget_id,
        **request.model_dump(exclude_unset=True)
    )


@router.delete("/{dashboard_id}/widgets/{widget_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_widget(
    dashboard_id: int,
    widget_id: int,
    dash_svc: DashboardService = Depends(get_dashboard_service),
    current_user: User = Depends(get_current_user),
) -> Response:
    """Remove a widget from a dashboard."""
    # Ensure ownership check
    await dash_svc.get_dashboard(dashboard_id=dashboard_id, user_id=current_user.id)
    await dash_svc.delete_widget(widget_id=widget_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)

