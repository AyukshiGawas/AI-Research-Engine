"""Document chunking service — sliding-window text splitter.

Responsibilities:
  1. Fetch a PROCESSED Document and validate it has extracted text.
  2. Split the extracted text into overlapping chunks respecting word boundaries.
  3. Delete any pre-existing chunks for the document (idempotent re-chunking).
  4. Persist new DocumentChunk records via ChunkRepository.
  5. Return the list of persisted chunks.

Clean Architecture:
  - No FastAPI dependencies or HTTPExceptions.
  - Domain exceptions only.
  - All DB operations via ChunkRepository and DocumentRepository.
"""

import uuid
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.exceptions import ChunkingError, DocumentNotFoundError, DocumentProcessingError
from app.models.document import DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.repositories.chunk_repository import ChunkRepository
from app.repositories.document_repository import DocumentRepository


class ChunkingService:
    """Splits a processed document's extracted text into overlapping chunks."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)
        self.chunk_repo = ChunkRepository(db)

    async def chunk_document(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Split extracted text into chunks and persist them.

        Args:
            document_id: UUID of the PROCESSED document to chunk.

        Returns:
            List of persisted DocumentChunk instances.

        Raises:
            DocumentNotFoundError: Document record does not exist.
            DocumentProcessingError: Document has not been successfully processed yet.
            ChunkingError: An unexpected error occurred during chunking.
        """
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document {document_id} not found.")

        if document.status != DocumentStatus.PROCESSED:
            raise DocumentProcessingError(
                f"Document {document_id} must be in PROCESSED status before chunking "
                f"(current status: {document.status.value})."
            )

        if not document.extracted_text:
            raise DocumentProcessingError(
                f"Document {document_id} has no extracted text available for chunking."
            )

        try:
            # Remove any existing chunks so re-chunking is idempotent
            deleted = await self.chunk_repo.delete_by_document(document_id)
            if deleted:
                logger.info(
                    f"CHUNKING | Deleted {deleted} existing chunks | id={document_id}"
                )

            raw_chunks = self._split_text(
                text=document.extracted_text,
                chunk_size=settings.CHUNK_SIZE,
                overlap=settings.CHUNK_OVERLAP,
            )

            orm_chunks = [
                DocumentChunk(
                    document_id=document_id,
                    chunk_index=idx,
                    chunk_text=text,
                    chunk_size=len(text),
                    start_char=start,
                    end_char=end,
                )
                for idx, (text, start, end) in enumerate(raw_chunks)
            ]

            persisted = await self.chunk_repo.create_bulk(orm_chunks)

            logger.info(
                f"CHUNKING | Created {len(persisted)} chunks | id={document_id} "
                f"| chunk_size={settings.CHUNK_SIZE} | overlap={settings.CHUNK_OVERLAP}"
            )
            return persisted

        except (DocumentNotFoundError, DocumentProcessingError):
            raise
        except Exception as exc:
            logger.error(f"CHUNKING | Unexpected failure | id={document_id} | error={exc}")
            raise ChunkingError(f"Failed to chunk document {document_id}: {exc}") from exc

    @staticmethod
    def _split_text(
        text: str,
        chunk_size: int,
        overlap: int,
    ) -> List[tuple[str, int, int]]:
        """Split text into overlapping segments aligned on word boundaries.

        Args:
            text: The full extracted text string.
            chunk_size: Target maximum character count per chunk.
            overlap: Number of trailing characters from the previous chunk
                     to repeat at the start of the next chunk.

        Returns:
            List of (chunk_text, start_char, end_char) tuples.
        """
        if not text or chunk_size <= 0:
            return []

        stride = max(1, chunk_size - overlap)
        chunks: List[tuple[str, int, int]] = []
        start = 0
        text_len = len(text)

        while start < text_len:
            end = min(start + chunk_size, text_len)

            # Extend to the next word boundary unless we are at the end
            if end < text_len:
                boundary = text.rfind(" ", start, end + 1)
                if boundary > start:
                    end = boundary

            segment = text[start:end].strip()
            if segment:
                chunks.append((segment, start, end))

            if end >= text_len:
                break

            start = start + stride

        return chunks
