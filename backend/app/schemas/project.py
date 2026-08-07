"""Pydantic schemas for Project entity."""

import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    """Schema for creating a minimal project workspace."""

    name: str = Field(..., min_length=1, max_length=255, description="Project workspace title")
    description: Optional[str] = Field(None, max_length=1000, description="Project summary")


class ProjectRead(BaseModel):
    """Schema for project details response."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    owner_id: uuid.UUID
    name: str
    description: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
