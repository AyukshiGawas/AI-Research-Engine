"""Database repository layer for User entity."""

import uuid
from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    """Encapsulates database operations for Users."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """Fetch user by primary UUID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Fetch user by email address."""
        stmt = select(User).where(User.email == email.lower())
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        """Fetch user by username."""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_identifier(self, identifier: str) -> Optional[User]:
        """Fetch user by either email or username."""
        stmt = select(User).where(
            (User.email == identifier.lower()) | (User.username == identifier)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        """Add user entity to database."""
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def update_last_login(self, user_id: uuid.UUID) -> None:
        """Update last login timestamp for user."""
        user = await self.get_by_id(user_id)
        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.flush()
