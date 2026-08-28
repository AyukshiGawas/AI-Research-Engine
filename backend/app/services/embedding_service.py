"""Embedding service — generates and stores vector embeddings for document chunks.

Responsibilities:
  1. Load all DocumentChunk records for a document via ChunkRepository.
  2. Route to the configured embedding provider (local or openai).
  3. Serialise each embedding vector as a JSON array string.
  4. Persist embedding metadata back to the chunk records.
  5. Return updated chunks.

Providers:
  - "local": Uses sentence-transformers library (model all-MiniLM-L6-v2 by default).
    The model is downloaded on first use and cached in ~/.cache/huggingface.
  - "openai": Calls the OpenAI Embeddings API using OPENAI_API_KEY from settings.

Clean Architecture:
  - No FastAPI dependencies or HTTPExceptions.
  - Domain exceptions only.
  - All DB operations via ChunkRepository.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.exceptions import EmbeddingError
from app.models.document_chunk import DocumentChunk
from app.repositories.chunk_repository import ChunkRepository


class EmbeddingService:
    """Generates and stores vector embeddings for DocumentChunk records."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.chunk_repo = ChunkRepository(db)

    async def embed_document(self, document_id: uuid.UUID) -> List[DocumentChunk]:
        """Generate and persist embeddings for all chunks of a document.

        Args:
            document_id: UUID of the document whose chunks to embed.

        Returns:
            List of updated DocumentChunk instances with embeddings.

        Raises:
            EmbeddingError: Provider is misconfigured or embedding generation failed.
        """
        chunks = await self.chunk_repo.get_by_document(document_id)
        if not chunks:
            logger.warning(
                f"EMBEDDING | No chunks found | id={document_id} — skipping embedding"
            )
            return []

        provider = settings.EMBEDDING_PROVIDER.lower()

        try:
            if provider == "openai":
                vectors = await self._embed_openai([c.chunk_text for c in chunks])
            else:
                vectors = self._embed_local([c.chunk_text for c in chunks])
        except Exception as exc:
            logger.error(f"EMBEDDING | Provider error | provider={provider} | error={exc}")
            raise EmbeddingError(
                f"Embedding generation failed for document {document_id}: {exc}"
            ) from exc

        generated_at = datetime.now(timezone.utc)
        model_name = (
            settings.EMBEDDING_MODEL
            if provider == "local"
            else f"openai/{settings.EMBEDDING_MODEL}"
        )

        updated: List[DocumentChunk] = []
        for chunk, vector in zip(chunks, vectors):
            embedding_json = json.dumps(vector)
            updated_chunk = await self.chunk_repo.update_embedding(
                chunk=chunk,
                embedding_json=embedding_json,
                model_name=model_name,
                generated_at=generated_at,
            )
            updated.append(updated_chunk)

        logger.info(
            f"EMBEDDING | Generated {len(updated)} embeddings | id={document_id} "
            f"| model={model_name} | provider={provider}"
        )
        return updated

    async def embed_query(self, query: str) -> List[float]:
        """Convert a single query string into an embedding vector.

        Uses the same provider and model configuration as ``embed_document``
        so query vectors are compatible with stored chunk vectors.

        Args:
            query: Natural-language search query string.

        Returns:
            Embedding vector as a list of floats.

        Raises:
            EmbeddingError: Provider is misconfigured or embedding failed.
        """
        provider = settings.EMBEDDING_PROVIDER.lower()
        try:
            if provider == "openai":
                vectors = await self._embed_openai([query])
            else:
                vectors = self._embed_local([query])
        except Exception as exc:
            logger.error(
                f"EMBEDDING | Query embed error | provider={provider} | error={exc}"
            )
            raise EmbeddingError(
                f"Query embedding generation failed: {exc}"
            ) from exc

        return vectors[0]

    def _embed_local(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using sentence-transformers (local, CPU/GPU).

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).

        Raises:
            EmbeddingError: sentence-transformers not installed or encoding failed.
        """
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
        except ImportError as exc:
            raise EmbeddingError(
                "sentence-transformers is not installed. "
                "Run: pip install sentence-transformers"
            ) from exc

        model = SentenceTransformer(settings.EMBEDDING_MODEL)
        embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return [emb.tolist() for emb in embeddings]

    async def _embed_openai(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using the OpenAI Embeddings API.

        Args:
            texts: List of text strings to embed.

        Returns:
            List of embedding vectors (list of floats).

        Raises:
            EmbeddingError: openai package not installed, key missing, or API error.
        """
        if not settings.OPENAI_API_KEY:
            raise EmbeddingError(
                "OPENAI_API_KEY must be set when EMBEDDING_PROVIDER=openai."
            )

        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError as exc:
            raise EmbeddingError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        response = await client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=texts,
        )
        return [item.embedding for item in response.data]
