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

    processed_at: Optional[datetime] = None
    extracted_text: Optional[str] = None
    processing_error: Optional[str] = None
    page_count: Optional[int] = None
    word_count: Optional[int] = None

    created_at: datetime
    updated_at: datetime


class DocumentUploadResponse(BaseModel):
    """Lightweight response returned immediately after a successful upload."""

    id: uuid.UUID
    original_filename: str
    file_size: int
    status: DocumentStatus
    message: str = "Document uploaded successfully."


class DocumentProcessResponse(BaseModel):
    """Response returned when triggering document processing."""

    id: uuid.UUID
    status: DocumentStatus
    processed_at: Optional[datetime] = None
    word_count: Optional[int] = None
    page_count: Optional[int] = None
    processing_error: Optional[str] = None
    message: str = "Document processing completed."


class DocumentDeleteResponse(BaseModel):
    """Confirmation payload returned after a document is deleted."""

    message: str = "Document deleted successfully."


class ChunkRead(BaseModel):
    """Single document chunk metadata returned by the API.

    The embedding field is omitted from list responses to keep payload size small;
    callers can retrieve it per-chunk if needed.
    """

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    document_id: uuid.UUID
    chunk_index: int
    chunk_text: str
    chunk_size: int
    start_char: int
    end_char: int
    embedding_model: Optional[str] = None
    embedding_generated_at: Optional[datetime] = None
    created_at: datetime


class ChunkListResponse(BaseModel):
    """Paginated list of chunks with summary statistics."""

    document_id: uuid.UUID
    total_chunks: int
    chunks: list[ChunkRead]
