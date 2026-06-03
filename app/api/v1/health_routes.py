"""Health check and diagnostics API routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.core.dependencies import get_health_monitor
from app.observability.monitoring import HealthMonitor

router = APIRouter(prefix="/health", tags=["Health & Diagnostics"])


@router.get("", status_code=status.HTTP_200_OK)
async def check_health(
    monitor: HealthMonitor = Depends(get_health_monitor),
) -> dict:
    """Retrieve database, cache, vector store, and LLM API connectivity status."""
    return await monitor.check_health()


@router.get("/metrics")
async def get_metrics() -> Response:
    """Prometheus metrics scrape endpoint."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
