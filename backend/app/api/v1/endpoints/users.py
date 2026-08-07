"""User endpoints module."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.user import UserRead, UserUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/me", response_model=UserRead)
async def read_user_me(
    current_user: User = Depends(get_current_active_user),
) -> UserRead:
    """Fetch profile data for the authenticated user."""
    return current_user


@router.put("/me", response_model=UserRead)
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Update profile details for the authenticated user."""
    user_service = UserService(db)
    updated_user = await user_service.update_profile(current_user.id, user_update)
    return updated_user
