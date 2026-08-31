"""User profile management service."""

import uuid
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserRoleUpdate, UserStatusUpdate, UserUpdate
from app.services.audit_service import AuditService


class UserService:
    """Business logic for User operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = UserRepository(db)
        self.audit_service = AuditService(db)

    async def list_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Fetch a paginated list of all users."""
        return await self.repo.get_all(skip=skip, limit=limit)

    async def get_profile(self, user_id: uuid.UUID) -> User:
        """Fetch user profile by UUID."""
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user

    async def update_profile(self, user_id: uuid.UUID, user_update: UserUpdate) -> User:
        """Update authenticated user profile details."""
        user = await self.get_profile(user_id)

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

    async def update_status(
        self,
        user_id: uuid.UUID,
        status_in: UserStatusUpdate,
        admin_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Update a user's active status and record an audit log event."""
        user = await self.get_profile(user_id)
        old_status = user.is_active
        user.is_active = status_in.is_active
        await self.repo.db.flush()

        await self.audit_service.record_event(
            event_type="ADMIN_USER_STATUS_UPDATED",
            user_id=admin_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_user_id": str(user.id),
                "target_username": user.username,
                "previous_status": old_status,
                "new_status": user.is_active,
            },
        )
        return user

    async def update_role(
        self,
        user_id: uuid.UUID,
        role_in: UserRoleUpdate,
        admin_user: User,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> User:
        """Update a user's role and record an audit log event."""
        user = await self.get_profile(user_id)
        old_role = user.role
        user.role = role_in.role
        await self.repo.db.flush()

        await self.audit_service.record_event(
            event_type="ADMIN_USER_ROLE_UPDATED",
            user_id=admin_user.id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "target_user_id": str(user.id),
                "target_username": user.username,
                "previous_role": old_role,
                "new_role": user.role,
            },
        )
        return user
