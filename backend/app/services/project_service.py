"""Project workspace management service."""

import uuid
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project
from app.repositories.project_repository import ProjectRepository
from app.schemas.project import ProjectCreate


class ProjectService:
    """Business logic for Project entities."""

    def __init__(self, db: AsyncSession) -> None:
        self.repo = ProjectRepository(db)

    async def list_projects(self, owner_id: uuid.UUID) -> List[Project]:
        """Fetch project workspace list for user."""
        return await self.repo.list_by_owner(owner_id)

    async def create_project(self, owner_id: uuid.UUID, project_in: ProjectCreate) -> Project:
        """Create new project workspace for user."""
        project = Project(
            owner_id=owner_id,
            name=project_in.name,
            description=project_in.description,
            status="active",
        )
        return await self.repo.create(project)
