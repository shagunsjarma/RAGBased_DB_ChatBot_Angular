"""Async MySQL engine management."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy import text

from app.core.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    """Return the current async engine (must call ``init_db`` first)."""
    if _engine is None:
        raise RuntimeError("Database engine not initialised. Call init_db() first.")
    return _engine


async def init_db() -> AsyncEngine:
    """Create and return the global async MySQL engine."""
    global _engine
    settings = get_settings()
    _engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=20,
        max_overflow=10,
        pool_recycle=3600,
        pool_pre_ping=True,
        echo=settings.DEBUG,
    )
    return _engine


async def close_db() -> None:
    """Dispose of the global engine and release connection pool."""
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None


async def health_check() -> bool:
    """Return ``True`` if a simple ``SELECT 1`` succeeds."""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False
