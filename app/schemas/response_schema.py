"""Generic API response wrappers."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standard envelope for every API response."""
    success: bool = True
    message: str = "OK"
    data: T | None = None
    errors: list[str] | None = None
    request_id: str | None = None


class PaginatedResponse(BaseModel, Generic[T]):
    """Paginated list wrapper."""
    items: list[T]
    total: int
    page: int
    page_size: int
    total_pages: int
