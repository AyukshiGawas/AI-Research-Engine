"""Document management API endpoints.

All business logic is delegated to DocumentService.
Route handlers only perform I/O wiring (request parsing, response serialisation).
"""

from typing import List
import uuid

from fastapi import APIRouter, Depends, File, Request, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.models.user import User
from app.schemas.document import (
    DocumentDeleteResponse,
    DocumentProcessResponse,
    DocumentRead,
    DocumentUploadResponse,
)
from app.services.document_service import DocumentService

router = APIRouter()


@router.post(
    "/{project_id}/documents",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a research document",
)
async def upload_document(
    request: Request,
    project_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentUploadResponse:
    """Upload a single research document (PDF, DOCX, TXT, MD) to a project workspace.

    - **Max size**: 25 MB
    - **Allowed types**: pdf, docx, txt, md
    - **Storage**: Binary stored on disk; only metadata persisted in PostgreSQL
    - **Duplicate detection**: Identical files (same SHA-256 hash) within the same
      project are rejected with HTTP 409.
    """
    document_service = DocumentService(db)
    document = await document_service.upload_document(
        project_id=project_id,
        upload=file,
        uploader_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return DocumentUploadResponse(
        id=document.id,
        original_filename=document.original_filename,
        file_size=document.file_size,
        status=document.status,
    )


@router.post(
    "/{project_id}/documents/{document_id}/process",
    response_model=DocumentProcessResponse,
    summary="Trigger or re-trigger document text extraction processing",
)
async def process_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentProcessResponse:
    """Extract text and metadata from an uploaded research document."""
    document_service = DocumentService(db)
    document = await document_service.process_document(project_id, document_id, current_user.id)
    return DocumentProcessResponse(
        id=document.id,
        status=document.status,
        processed_at=document.processed_at,
        word_count=document.word_count,
        page_count=document.page_count,
        processing_error=document.processing_error,
    )


@router.get(
    "/{project_id}/documents",
    response_model=List[DocumentRead],
    summary="List all documents in a project workspace",
)
async def list_documents(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> List[DocumentRead]:
    """Return metadata for every document belonging to the given project workspace."""
    document_service = DocumentService(db)
    return await document_service.list_documents(project_id, current_user.id)


@router.get(
    "/{project_id}/documents/{document_id}",
    response_model=DocumentRead,
    summary="Retrieve document metadata",
)
async def get_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentRead:
    """Return detailed metadata for a single document."""
    document_service = DocumentService(db)
    return await document_service.get_document(project_id, document_id, current_user.id)


@router.get(
    "/{project_id}/documents/{document_id}/download",
    summary="Download a document file",
)
async def download_document(
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> FileResponse:
    """Stream the physical file back to the authorised user.

    Sets ``Content-Disposition: attachment`` using the original filename.
    """
    document_service = DocumentService(db)
    descriptor = await document_service.get_download_descriptor(
        project_id, document_id, current_user.id
    )
    return FileResponse(
        path=descriptor.path,
        filename=descriptor.filename,
        media_type=descriptor.mime_type,
    )


@router.delete(
    "/{project_id}/documents/{document_id}",
    response_model=DocumentDeleteResponse,
    summary="Delete a document",
)
async def delete_document(
    request: Request,
    project_id: uuid.UUID,
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> DocumentDeleteResponse:
    """Delete document metadata from PostgreSQL and remove the physical file from disk."""
    document_service = DocumentService(db)
    await document_service.delete_document(
        project_id=project_id,
        document_id=document_id,
        requester_id=current_user.id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    return DocumentDeleteResponse()

