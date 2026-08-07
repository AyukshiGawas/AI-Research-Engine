"""Database repository layer for Document entity.

All SQL interactions are isolated here.  Services call this layer; no raw
SQLAlchemy expressions should appear in service or endpoint code.
"""

from datetime import datetime
import uuid
from typing import List, Optional


from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus


class DocumentRepository:
    """Encapsulates database CRUD operations for Documents."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, document: Document) -> Document:
        """Persist a new Document record and return it with server-set fields."""
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Optional[Document]:
        """Fetch a document by its UUID primary key.

        Args:
            document_id: UUID of the requested document.

        Returns:
            Document ORM instance or ``None`` if not found.
        """
        stmt = select(Document).where(Document.id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id_and_project(
        self, document_id: uuid.UUID, project_id: uuid.UUID
    ) -> Optional[Document]:
        """Fetch a document ensuring it belongs to the given project (IDOR guard).

        Args:
            document_id: UUID of the requested document.
            project_id: UUID of the owning project workspace.

        Returns:
            Document ORM instance or ``None`` if not found or ownership mismatch.
        """
        stmt = select(Document).where(
            Document.id == document_id,
            Document.project_id == project_id,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_project(self, project_id: uuid.UUID) -> List[Document]:
        """Return all documents for a project, newest first.

        Args:
            project_id: UUID of the owning project workspace.

        Returns:
            List of Document ORM instances ordered by ``created_at`` descending.
        """
        stmt = (
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_content_hash(
        self, project_id: uuid.UUID, content_hash: str
    ) -> Optional[Document]:
        """Check if an identical file has already been uploaded to this project.

        Args:
            project_id: UUID of the target project workspace.
            content_hash: SHA-256 hex digest of the candidate file.

        Returns:
            Existing Document if a duplicate is found, else ``None``.
        """
        stmt = select(Document).where(
            Document.project_id == project_id,
            Document.storage_path == content_hash,
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def update_status(
        self, document: Document, status: DocumentStatus
    ) -> Document:
        """Update the lifecycle status of a document record.

        Args:
            document: Document ORM instance to update.
            status: New ``DocumentStatus`` value.

        Returns:
            Updated Document instance.
        """
        document.status = status
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def update_processing_success(
        self,
        document: Document,
        extracted_text: str,
        page_count: Optional[int],
        word_count: Optional[int],
        processed_at: datetime,
    ) -> Document:
        """Update document record with extracted text and processing metadata on success.

        Args:
            document: Document ORM instance to update.
            extracted_text: Extracted plain text string.
            page_count: Extracted page count (if applicable).
            word_count: Extracted word count.
            processed_at: Timestamp when processing completed.

        Returns:
            Updated Document instance.
        """
        document.status = DocumentStatus.PROCESSED
        document.extracted_text = extracted_text
        document.page_count = page_count
        document.word_count = word_count
        document.processed_at = processed_at
        document.processing_error = None
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def update_processing_failure(
        self,
        document: Document,
        error_message: str,
    ) -> Document:
        """Update document record with error details on processing failure.

        Args:
            document: Document ORM instance to update.
            error_message: Detailed error string describing extraction failure.

        Returns:
            Updated Document instance.
        """
        document.status = DocumentStatus.FAILED
        document.processing_error = error_message
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def delete(self, document: Document) -> None:
        """Delete a document record from the database.

        Args:
            document: Document ORM instance to remove.
        """
        await self.db.delete(document)
        await self.db.flush()

