"""FastAPI dependencies for dependency injection."""

from __future__ import annotations

from typing import AsyncGenerator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import get_current_user_id


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Yield an ``AsyncSession`` from the application's session factory."""
    session_factory = request.app.state.session_factory
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


async def get_redis(request: Request):
    """Return the Redis client stored on ``app.state``."""
    return request.app.state.redis_client


async def get_qdrant(request: Request):
    """Return the Qdrant client stored on ``app.state``."""
    return request.app.state.qdrant_client


def get_app_settings() -> Settings:
    """Return the cached ``Settings`` singleton."""
    return get_settings()


async def get_current_user(
    user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """FastAPI dependency – returns the active User object based on JWT payload."""
    from app.models.user_model import User
    from app.core.exceptions import AuthenticationError

    user = await db.get(User, user_id)
    if not user or not user.is_active:
        raise AuthenticationError("User is inactive or not found")
    return user


async def get_llm_service(request: Request):
    """Return the LLMService singleton from application state."""
    return request.app.state.llm_service


async def get_sql_service(request: Request):
    """Return the SQLService singleton from application state."""
    return request.app.state.sql_service


async def get_cache_service(request: Request):
    """Return the CacheService singleton from application state."""
    return request.app.state.cache_service


async def get_rag_service(request: Request):
    """Return the RAGService singleton from application state."""
    return request.app.state.rag_service


async def get_chat_service(request: Request, db: AsyncSession = Depends(get_db_session)):
    """Return a request-scoped ChatService instance bound to the current DB session."""
    from app.services.chat_service import ChatService
    from app.repositories.chat_repository import ChatRepository
    
    state_chat = request.app.state.chat_service
    return ChatService(
        chat_repo=ChatRepository(db),
        orchestration_agent=state_chat._orchestrator,
        summarization_agent=state_chat._summarizer,
    )


async def get_dashboard_service(request: Request, db: AsyncSession = Depends(get_db_session)):
    """Return a request-scoped DashboardService instance bound to the current DB session."""
    from app.services.dashboard_service import DashboardService
    from app.repositories.dashboard_repository import DashboardRepository
    
    return DashboardService(
        dashboard_repo=DashboardRepository(db),
    )



async def get_health_monitor(request: Request):
    """Return an instantiated HealthMonitor."""
    from app.observability.monitoring import HealthMonitor
    return HealthMonitor(
        db_engine=request.app.state.db_engine,
        redis_client=request.app.state.redis_client,
        qdrant_client=request.app.state.qdrant_client,
        llm_service=request.app.state.llm_service,
    )




