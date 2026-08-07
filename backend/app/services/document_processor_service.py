"""Document processing service — text extraction pipeline orchestrator.

Responsibilities:
  1. Fetch Document record from database repository.
  2. Transition status from UPLOADED -> PROCESSING.
  3. Resolve disk file location via StorageProvider.
  4. Select format extractor via ExtractorFactory.
  5. Extract plain text content and metadata (page count, word count).
  6. Validate extraction results.
  7. Update status to PROCESSED and record extracted text in database.
  8. Catch processing/extraction errors, transition status to FAILED, and record error details.

Clean Architecture:
  - No FastAPI dependencies or HTTPExceptions.
  - Domain exceptions only.
  - All DB operations via DocumentRepository.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.core.storage import storage_provider
from app.exceptions import (
    DocumentExtractionError,
    DocumentNotFoundError,
    DocumentProcessingError,
    UnsupportedDocumentTypeError,
)
from app.models.document import Document, DocumentStatus
from app.repositories.document_repository import DocumentRepository
from app.services.extractors.factory import ExtractorFactory


class DocumentProcessorService:
    """Orchestrates document text extraction and status updates."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.doc_repo = DocumentRepository(db)

    async def process_document(self, document_id: uuid.UUID) -> Document:
        """Process an uploaded document by extracting its text content.

        Args:
            document_id: UUID of the document to process.

        Returns:
            Updated Document ORM instance.

        Raises:
            DocumentNotFoundError: Document record not found.
        """
        document = await self.doc_repo.get_by_id(document_id)
        if not document:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found.")

        # Transition status: UPLOADED -> PROCESSING
        await self.doc_repo.update_status(document, DocumentStatus.PROCESSING)
        logger.info(f"DOCUMENT PROCESSOR | Status updated to PROCESSING | id={document.id}")

        try:
            # Resolve physical file path on disk
            file_path = storage_provider.resolve(document.storage_path)

            if not file_path.exists():
                raise DocumentProcessingError(f"File not found on disk: {document.storage_path}")

            # Select appropriate extractor using factory pattern
            extractor = ExtractorFactory.get_extractor(document.extension)

            # Perform text extraction
            result = extractor.extract(file_path)

            # Update DB record with extracted text and transition: PROCESSING -> PROCESSED
            processed_at = datetime.now(timezone.utc)
            updated_doc = await self.doc_repo.update_processing_success(
                document=document,
                extracted_text=result.text,
                page_count=result.page_count,
                word_count=result.word_count,
                processed_at=processed_at,
            )
            logger.info(
                f"DOCUMENT PROCESSOR | Status updated to PROCESSED | id={document.id} | "
                f"words={result.word_count} | pages={result.page_count}"
            )
            return updated_doc

        except (UnsupportedDocumentTypeError, DocumentExtractionError, DocumentProcessingError) as exc:
            logger.error(f"DOCUMENT PROCESSOR | Extraction failed | id={document.id} | error={exc}")
            return await self.doc_repo.update_processing_failure(document, str(exc))

        except Exception as exc:
            error_msg = f"Unexpected error during processing: {str(exc)}"
            logger.error(f"DOCUMENT PROCESSOR | Unexpected failure | id={document.id} | error={exc}")
            return await self.doc_repo.update_processing_failure(document, error_msg)
