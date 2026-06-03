"""Chat repository – conversations & messages CRUD."""

from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import delete, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation_model import Conversation, Message


class ChatRepository:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_conversation(self, user_id: int, title: str | None = None) -> Conversation:
        conv = Conversation(user_id=user_id, title=title or "New Conversation")
        self._session.add(conv)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(conv)
        return conv

    async def get_conversation(self, conversation_id: int, user_id: int) -> Conversation | None:
        return await self._session.scalar(
            select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )

    async def list_conversations(self, user_id: int, skip: int = 0, limit: int = 20) -> tuple[list[Conversation], int]:
        total = await self._session.scalar(
            select(func.count()).select_from(Conversation).where(Conversation.user_id == user_id)
        ) or 0
        result = await self._session.execute(
            select(Conversation).where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all()), total

    async def update_conversation_title(self, conversation_id: int, title: str) -> None:
        await self._session.execute(
            update(Conversation).where(Conversation.id == conversation_id)
            .values(title=title, updated_at=dt.datetime.now(dt.timezone.utc))
        )
        await self._session.commit()

    async def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        await self._session.execute(delete(Message).where(Message.conversation_id == conversation_id))
        result = await self._session.execute(
            delete(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        )
        await self._session.commit()
        return result.rowcount > 0

    async def add_message(self, conversation_id: int, role: str, content: str, metadata_json: dict[str, Any] | None = None) -> Message:
        msg = Message(conversation_id=conversation_id, role=role, content=content, metadata_json=metadata_json)
        self._session.add(msg)
        await self._session.execute(
            update(Conversation).where(Conversation.id == conversation_id)
            .values(updated_at=dt.datetime.now(dt.timezone.utc))
        )
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(msg)
        return msg

    async def get_messages(self, conversation_id: int, skip: int = 0, limit: int = 50) -> list[Message]:
        result = await self._session.execute(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_recent_messages(self, conversation_id: int, limit: int = 10) -> list[Message]:
        result = await self._session.execute(
            select(Message).where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc()).limit(limit)
        )
        msgs = list(result.scalars().all())
        msgs.reverse()
        return msgs

    async def get_message_count(self, conversation_id: int) -> int:
        return await self._session.scalar(
            select(func.count()).select_from(Message).where(Message.conversation_id == conversation_id)
        ) or 0
