"""Async session factory and context managers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.mysql import get_engine

_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return (and lazily create) the global session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )
    return _session_factory


def init_session_factory(engine) -> async_sessionmaker[AsyncSession]:
    """Explicitly initialise the session factory with *engine*."""
    global _session_factory
    _session_factory = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Async generator dependency that yields an ``AsyncSession``."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def transaction() -> AsyncGenerator[AsyncSession, None]:
    """Context manager for explicit transaction control."""
    factory = get_session_factory()
    async with factory() as session:
        async with session.begin():
            yield session
