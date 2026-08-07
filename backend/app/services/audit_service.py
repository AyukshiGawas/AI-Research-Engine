"""Audit logging service for authentication and security events."""

import uuid
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.audit_log import AuditLog
from app.repositories.audit_repository import AuditRepository


class AuditService:
    """Service handling structured logging and database persistence of security events."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = AuditRepository(db)

    async def record_event(
        self,
        event_type: str,
        user_id: Optional[uuid.UUID] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record an audit event to both database and log stream."""
        logger.info(
            f"AUDIT | event={event_type} | user_id={user_id} | ip={ip_address} | details={details}"
        )
        audit_log = AuditLog(
            user_id=user_id,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details,
        )
        await self.repo.log_event(audit_log)
