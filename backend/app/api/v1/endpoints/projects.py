"""Project workspace API endpoints (Minimal GET and POST only)."""

from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectRead
from app.services.project_service import ProjectService

router = APIRouter()


@router.get("/", response_model=List[ProjectRead])
async def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[ProjectRead]:
    """Fetch project workspace list for current authenticated user."""
    project_service = ProjectService(db)
    return await project_service.list_projects(current_user.id)


@router.post("/", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProjectRead:
    """Create a new project workspace for current authenticated user."""
    project_service = ProjectService(db)
    return await project_service.create_project(current_user.id, project_in)
