"""Database repository layer for AuditLog entity."""

from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditRepository:
    """Encapsulates creation of security and auth audit logs."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log_event(self, audit_log: AuditLog) -> AuditLog:
        """Persist audit log entry to database."""
        self.db.add(audit_log)
        await self.db.flush()
        return audit_log
