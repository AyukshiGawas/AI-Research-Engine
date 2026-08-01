"""Document management service — the sole orchestrator of file upload business logic.

Responsibilities:
  1. Validate extension and file size.
  2. Read the upload stream into memory safely (size-capped).
  3. Compute SHA-256 hash for de-duplication.
  4. Verify project ownership to prevent IDOR.
  5. Persist binary data via StorageProvider.
  6. Create the Document DB record.
  7. Record audit events for every upload and deletion.

No business logic belongs in endpoint route handlers.
"""

import uuid
from pathlib import Path
from typing import List

from fastapi import HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.core.storage import compute_sha256, storage_provider
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.repositories.project_repository import ProjectRepository
from app.services.audit_service import AuditService

# Map allowed extensions to their canonical MIME types
_MIME_MAP: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
}

# Supported binary magic-byte prefixes (checked against first 8 bytes)
_MAGIC_BYTES: dict[str, list[bytes]] = {
    "pdf": [b"%PDF"],
    "docx": [b"PK\x03\x04"],  # DOCX is a ZIP-based format
    "txt": [],  # Plain text has no universal magic; extension check is sufficient
    "md": [],
}


class DocumentService:
    """Business logic for document upload, listing, detail retrieval, and deletion."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.project_repo = ProjectRepository(db)
        self.audit_service = AuditService(db)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _validate_extension(self, filename: str) -> str:
        """Extract and validate the file extension.

        Args:
            filename: Original client-supplied filename.

        Returns:
            Lowercase extension string WITHOUT leading dot (e.g. ``"pdf"``).

        Raises:
            HTTPException 400: Extension is empty or not in the allow-list.
        """
        ext = Path(filename).suffix.lstrip(".").lower()
        if not ext or ext not in settings.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Unsupported file type '.{ext}'. "
                    f"Allowed: {', '.join(settings.ALLOWED_EXTENSIONS)}"
                ),
            )
        return ext

    def _validate_magic_bytes(self, data: bytes, extension: str) -> None:
        """Check binary magic bytes match the declared extension.

        Only PDF and DOCX have deterministic magic signatures.
        TXT and MD are skipped — content-based detection is unreliable for UTF-8 text.

        Args:
            data: Raw file bytes (at least first 8 bytes are sufficient).
            extension: Already-validated lowercase extension.

        Raises:
            HTTPException 400: Magic bytes don't match the declared type.
        """
        expected_magic = _MAGIC_BYTES.get(extension, [])
        if not expected_magic:
            return  # No magic signature for this type; skip check

        header = data[:8]
        if not any(header.startswith(magic) for magic in expected_magic):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"File content does not match the declared type '.{extension}'. "
                    "Please upload an unmodified file."
                ),
            )

    async def _read_upload_stream(self, upload: UploadFile) -> bytes:
        """Read the entire upload stream, enforcing the size cap.

        Args:
            upload: FastAPI ``UploadFile`` object.

        Returns:
            Full file contents as bytes.

        Raises:
            HTTPException 413: Accumulated bytes exceed ``MAX_UPLOAD_SIZE_BYTES``.
        """
        max_bytes = settings.MAX_UPLOAD_SIZE_BYTES
        chunks: list[bytes] = []
        total_bytes = 0

        while True:
            chunk = await upload.read(1024 * 64)  # 64 KB chunks
            if not chunk:
                break
            total_bytes += len(chunk)
            if total_bytes > max_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=(
                        f"File exceeds the maximum allowed size of "
                        f"{max_bytes // (1024 * 1024)} MB."
                    ),
                )
            chunks.append(chunk)

        return b"".join(chunks)

    async def _assert_project_ownership(
        self, project_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Verify the current user owns the target project.

        Args:
            project_id: UUID of the project workspace.
            user_id: UUID of the currently authenticated user.

        Raises:
            HTTPException 404: Project does not exist.
            HTTPException 403: Project exists but belongs to another user.
        """
        project = await self.project_repo.get_by_id(project_id)
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project workspace not found.",
            )
        if project.owner_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have access to this project workspace.",
            )

    # ------------------------------------------------------------------
    # Public service methods
    # ------------------------------------------------------------------

    async def upload_document(
        self,
        project_id: uuid.UUID,
        upload: UploadFile,
        uploader_id: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> Document:
        """Validate, store, and record a new research document.

        Workflow:
          1. Assert project ownership (IDOR prevention).
          2. Validate extension.
          3. Read stream with size enforcement.
          4. Validate magic bytes.
          5. Compute SHA-256; reject exact duplicates within the same project.
          6. Write file via StorageProvider.
          7. Persist Document record in PostgreSQL.
          8. Emit audit log.

        Args:
            project_id: Target project workspace UUID.
            upload: Incoming multipart file stream.
            uploader_id: UUID of the authenticated user performing the upload.
            ip_address: Request IP for audit log.
            user_agent: Request User-Agent header for audit log.

        Returns:
            Newly created Document ORM instance.
        """
        await self._assert_project_ownership(project_id, uploader_id)

        original_filename = upload.filename or "unknown"
        ext = self._validate_extension(original_filename)
        data = await self._read_upload_stream(upload)
        self._validate_magic_bytes(data, ext)

        content_hash = compute_sha256(data)

        # De-duplication: reject identical content already in this project
        existing = await self.doc_repo.get_by_content_hash(project_id, content_hash)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    f"An identical file '{existing.original_filename}' already exists "
                    "in this project workspace."
                ),
            )

        document_id = uuid.uuid4()
        stored_filename = f"{document_id}.{ext}"
        mime_type = _MIME_MAP.get(ext, "application/octet-stream")

        # Write to disk (atomic: DB commit happens after; on failure we clean up)
        storage_path = await storage_provider.save(
            project_id=project_id,
            document_id=document_id,
            extension=ext,
            data=data,
        )

        document = Document(
            id=document_id,
            project_id=project_id,
            uploaded_by=uploader_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            storage_path=storage_path,
            mime_type=mime_type,
            extension=ext,
            file_size=len(data),
            status=DocumentStatus.UPLOADED,
        )

        try:
            created = await self.doc_repo.create(document)
        except Exception as exc:
            # Atomic cleanup: remove orphaned file on DB failure
            await storage_provider.delete(storage_path)
            logger.error(f"DOCUMENT | DB persist failed; disk file cleaned up | {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to persist document record.",
            ) from exc

        await self.audit_service.record_event(
            event_type="DOCUMENT_UPLOAD_SUCCESS",
            user_id=uploader_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "document_id": str(document_id),
                "project_id": str(project_id),
                "filename": original_filename,
                "size_bytes": len(data),
            },
        )

        logger.info(
            f"DOCUMENT | uploaded | id={document_id} | project={project_id} "
            f"| file={original_filename} | size={len(data)}"
        )
        return created

    async def list_documents(
        self, project_id: uuid.UUID, requester_id: uuid.UUID
    ) -> List[Document]:
        """Return all documents for a project the requester owns.

        Args:
            project_id: Target project workspace UUID.
            requester_id: Authenticated user UUID (ownership check).

        Returns:
            List of Document ORM instances.
        """
        await self._assert_project_ownership(project_id, requester_id)
        return await self.doc_repo.list_by_project(project_id)

    async def get_document(
        self,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
        requester_id: uuid.UUID,
    ) -> Document:
        """Return a single document's metadata.

        Args:
            project_id: Target project workspace UUID.
            document_id: Target document UUID.
            requester_id: Authenticated user UUID (ownership check).

        Returns:
            Document ORM instance.

        Raises:
            HTTPException 404: Document not found in this project.
        """
        await self._assert_project_ownership(project_id, requester_id)
        document = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this project workspace.",
            )
        return document

    async def delete_document(
        self,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
        requester_id: uuid.UUID,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Delete document metadata from PostgreSQL and remove the physical file.

        Args:
            project_id: Target project workspace UUID.
            document_id: Target document UUID.
            requester_id: Authenticated user UUID (ownership check).
            ip_address: Request IP for audit log.
            user_agent: Request User-Agent for audit log.
        """
        await self._assert_project_ownership(project_id, requester_id)
        document = await self.doc_repo.get_by_id_and_project(document_id, project_id)
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in this project workspace.",
            )

        storage_path = document.storage_path
        original_filename = document.original_filename

        # Remove DB record first; disk cleanup follows
        await self.doc_repo.delete(document)
        await storage_provider.delete(storage_path)

        await self.audit_service.record_event(
            event_type="DOCUMENT_DELETE",
            user_id=requester_id,
            ip_address=ip_address,
            user_agent=user_agent,
            details={
                "document_id": str(document_id),
                "project_id": str(project_id),
                "filename": original_filename,
            },
        )

        logger.info(
            f"DOCUMENT | deleted | id={document_id} | project={project_id} "
            f"| file={original_filename}"
        )
