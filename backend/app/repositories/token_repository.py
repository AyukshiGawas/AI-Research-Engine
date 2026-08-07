"""Database repository layer for RefreshToken entity."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.refresh_token import RefreshToken


class TokenRepository:
    """Encapsulates database operations for refresh tokens."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, token_record: RefreshToken) -> RefreshToken:
        """Store new refresh token record."""
        self.db.add(token_record)
        await self.db.flush()
        await self.db.refresh(token_record)
        return token_record

    async def get_by_hash(self, token_hash: str) -> Optional[RefreshToken]:
        """Retrieve token record by SHA-256 hash."""
        stmt = select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def revoke(self, token_record: RefreshToken, replaced_by_id: Optional[uuid.UUID] = None) -> None:
        """Mark token record as revoked."""
        token_record.is_revoked = True
        if replaced_by_id:
            token_record.replaced_by_id = replaced_by_id
        await self.db.flush()

    async def revoke_all_user_tokens(self, user_id: uuid.UUID) -> None:
        """Revoke all active refresh tokens for a user (e.g. on security reset)."""
        stmt = select(RefreshToken).where(
            RefreshToken.user_id == user_id, RefreshToken.is_revoked == False
        )
        result = await self.db.execute(stmt)
        tokens = result.scalars().all()
        for token in tokens:
            token.is_revoked = True
        await self.db.flush()
