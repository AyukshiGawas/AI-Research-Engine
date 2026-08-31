"""Admin User Management Endpoints — Phase 10.

Endpoints:
- GET /api/v1/admin/users: List all users (admin-only).
- GET /api/v1/admin/users/{user_id}: View specific user details (admin-only).
- PATCH /api/v1/admin/users/{user_id}/status: Activate/deactivate a user (admin-only).
- PATCH /api/v1/admin/users/{user_id}/role: Change a user's role (admin-only).
"""

import uuid
from typing import List

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_admin_user
from app.models.user import User
from app.schemas.user import UserRead, UserRoleUpdate, UserStatusUpdate
from app.services.user_service import UserService

router = APIRouter()


@router.get("/users", response_model=List[UserRead], summary="List all users")
async def list_users(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> List[UserRead]:
    """Fetch paginated list of all users. Admin privileges required."""
    service = UserService(db)
    users = await service.list_users(skip=skip, limit=limit)
    return users


@router.get("/users/{user_id}", response_model=UserRead, summary="Get user by ID")
async def get_user_by_id(
    user_id: uuid.UUID,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Fetch details of a specific user. Admin privileges required."""
    service = UserService(db)
    user = await service.get_profile(user_id)
    return user


@router.patch("/users/{user_id}/status", response_model=UserRead, summary="Update user active status")
async def update_user_status(
    user_id: uuid.UUID,
    status_in: UserStatusUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Activate or deactivate a user account. Admin privileges required."""
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    updated_user = await service.update_status(
        user_id=user_id,
        status_in=status_in,
        admin_user=current_admin,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return updated_user


@router.patch("/users/{user_id}/role", response_model=UserRead, summary="Update user role")
async def update_user_role(
    user_id: uuid.UUID,
    role_in: UserRoleUpdate,
    request: Request,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
) -> UserRead:
    """Change a user's role (e.g. admin, researcher, analyst). Admin privileges required."""
    service = UserService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    updated_user = await service.update_role(
        user_id=user_id,
        role_in=role_in,
        admin_user=current_admin,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    return updated_user
