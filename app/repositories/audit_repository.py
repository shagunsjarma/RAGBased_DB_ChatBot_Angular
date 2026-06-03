"""Audit repository – action logging."""

from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_model import AuditLog


class AuditRepository:
    __slots__ = ("_session",)

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log_action(self, user_id: int | None, action: str, resource_type: str,
                          resource_id: str | None = None, details: dict[str, Any] | None = None,
                          ip_address: str | None = None) -> AuditLog:
        entry = AuditLog(user_id=user_id, action=action, resource_type=resource_type,
                         resource_id=resource_id, details=details, ip_address=ip_address)
        self._session.add(entry)
        await self._session.flush()
        await self._session.commit()
        await self._session.refresh(entry)
        return entry

    async def get_user_audit_log(self, user_id: int, skip: int = 0, limit: int = 50) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog).where(AuditLog.user_id == user_id)
            .order_by(AuditLog.created_at.desc()).offset(skip).limit(limit)
        )
        return list(result.scalars().all())

    async def get_resource_audit_log(self, resource_type: str, resource_id: str) -> list[AuditLog]:
        result = await self._session.execute(
            select(AuditLog).where(AuditLog.resource_type == resource_type, AuditLog.resource_id == resource_id)
            .order_by(AuditLog.created_at.desc())
        )
        return list(result.scalars().all())
