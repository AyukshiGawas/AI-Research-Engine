"""User profile management service."""

import uuid
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserUpdate


class UserService:
    """Business logic for User operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)

    async def get_profile(self, user_id: uuid.UUID) -> User:
        """Fetch user profile by UUID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_44_NOT_FOUND if hasattr(status, 'HTTP_44_NOT_FOUND') else 404,
                detail="User not found",
            )
        return user

    async def update_profile(self, user_id: uuid.UUID, user_update: UserUpdate) -> User:
        """Update authenticated user profile details."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        if user_update.email and user_update.email != user.email:
            existing = await self.repo.get_by_email(user_update.email)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address already taken.",
                )
            user.email = user_update.email.lower()

        if user_update.full_name is not None:
            user.full_name = user_update.full_name

        if user_update.password:
            user.hashed_password = get_password_hash(user_update.password)

        await self.repo.db.flush()
        return user
