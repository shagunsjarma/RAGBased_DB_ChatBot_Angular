"""User repository – async CRUD for the users table."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import func, select, update, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user_model import User


class UserRepository:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, email: str, hashed_password: str, full_name: str | None = None, role: str = "user") -> User:
        user = User(email=email, hashed_password=hashed_password, full_name=full_name, role=role)
        self._session.add(user)
        try:
            await self._session.flush()
        except IntegrityError:
            await self._session.rollback()
            raise
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> User | None:
        return await self._session.scalar(select(User).where(User.id == user_id))

    async def get_by_email(self, email: str) -> User | None:
        return await self._session.scalar(select(User).where(User.email == email))

    async def list_users(self, skip: int = 0, limit: int = 20) -> tuple[list[User], int]:
        total: int = await self._session.scalar(select(func.count()).select_from(User)) or 0
        result = await self._session.execute(select(User).order_by(User.id).offset(skip).limit(limit))
        return list(result.scalars().all()), total

    async def update(self, user_id: int, **kwargs: Any) -> User | None:
        user = await self.get_by_id(user_id)
        if user is None:
            return None
        for k, v in kwargs.items():
            if hasattr(user, k):
                setattr(user, k, v)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(user)
        return user

    async def update_last_login(self, user_id: int) -> None:
        await self._session.execute(
            update(User).where(User.id == user_id).values(last_login_at=dt.datetime.now(dt.timezone.utc))
        )
        await self._session.commit()

    async def delete(self, user_id: int) -> bool:
        result = await self._session.execute(delete(User).where(User.id == user_id))
        await self._session.commit()
        return result.rowcount > 0
