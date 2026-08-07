"""Database repository layer for DocumentChunk entity.

All SQL interactions for document chunks are isolated here.
Services call this layer; no raw SQLAlchemy expressions appear
in service or endpoint code.
"""

import uuid
from typing import List, Optional

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document_chunk import DocumentChunk


class ChunkRepository:
    """Encapsulates database CRUD operations for DocumentChunk records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_bulk(self, chunks: List[DocumentChunk]) -> List[DocumentChunk]:
        """Persist a batch of DocumentChunk records in insertion order.

        Args:
            chunks: List of unsaved DocumentChunk ORM instances.

        Returns:
            The same list with server-generated IDs populated via flush/refresh.
        """
        for chunk in chunks:
            self.db.add(chunk)
        await self.db.flush()
        for chunk in chunks:
            await self.db.refresh(chunk)
        return chunks

    async def get_by_document(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Return all chunks for a document ordered by chunk_index ascending.

        Args:
            document_id: UUID of the parent document.

        Returns:
            List of DocumentChunk ORM instances ordered by chunk_index.
        """
        stmt = (
            select(DocumentChunk)
            .where(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.chunk_index)
        )
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def delete_by_document(self, document_id: uuid.UUID) -> int:
        """Delete all chunks belonging to a document.

        Args:
            document_id: UUID of the parent document.

        Returns:
            Number of rows deleted.
        """
        stmt = delete(DocumentChunk).where(DocumentChunk.document_id == document_id)
        result = await self.db.execute(stmt)
        await self.db.flush()
        return result.rowcount

    async def count_by_document(self, document_id: uuid.UUID) -> int:
        """Return the number of chunks for a given document.

        Args:
            document_id: UUID of the parent document.

        Returns:
            Integer count of persisted chunks.
        """
        stmt = select(func.count()).where(DocumentChunk.document_id == document_id)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_embedding(
        self,
        chunk: DocumentChunk,
        embedding_json: str,
        model_name: str,
        generated_at,
    ) -> DocumentChunk:
        """Write embedding data back onto an existing chunk record.

        Args:
            chunk: The DocumentChunk ORM instance to update.
            embedding_json: JSON-serialised float vector string.
            model_name: Name of the model that produced the embedding.
            generated_at: UTC datetime of generation.

        Returns:
            Updated DocumentChunk instance.
        """
        chunk.embedding = embedding_json
        chunk.embedding_model = model_name
        chunk.embedding_generated_at = generated_at
        await self.db.flush()
        await self.db.refresh(chunk)
        return chunk
