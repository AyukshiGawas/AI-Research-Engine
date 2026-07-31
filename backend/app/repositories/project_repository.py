"""Database repository layer for Project entity."""

import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.project import Project


class ProjectRepository:
    """Encapsulates database operations for Projects."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_by_owner(self, owner_id: uuid.UUID) -> List[Project]:
        """Fetch all projects owned by user."""
        stmt = (
            select(Project)
            .where(Project.owner_id == owner_id)
            .order_by(Project.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, project_id: uuid.UUID) -> Optional[Project]:
        """Fetch project by ID."""
        stmt = select(Project).where(Project.id == project_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, project: Project) -> Project:
        """Create new project workspace."""
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project
