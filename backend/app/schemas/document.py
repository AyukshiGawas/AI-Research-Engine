"""Pydantic schemas for Document entity requests and responses."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.document import DocumentStatus


class DocumentRead(BaseModel):
    """Full document metadata returned by the API.

    Never exposes binary content — only metadata persisted in PostgreSQL.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    project_id: uuid.UUID
    uploaded_by: Optional[uuid.UUID] = None

    original_filename: str
    stored_filename: str
    storage_path: str

    mime_type: str
    extension: str
    file_size: int

    status: DocumentStatus

    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Lightweight response returned immediately after a successful upload."""

    id: uuid.UUID
    original_filename: str
    file_size: int
    status: DocumentStatus
    message: str = "Document uploaded successfully."


class DocumentDeleteResponse(BaseModel):
    """Confirmation payload returned after a document is deleted."""

    message: str = "Document deleted successfully."
