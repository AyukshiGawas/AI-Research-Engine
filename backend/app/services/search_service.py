"""Search service — Phase 7: Semantic Search / Vector Retrieval.

Responsibilities:
  1. Embed the caller's text query using EmbeddingService.embed_query().
  2. Fetch all DocumentChunk records that have stored embeddings via
     ChunkRepository.get_all_with_embeddings().
  3. Compute cosine similarity in memory using numpy (no external vector DB).
  4. Sort results by similarity descending and return the top-K items.

Compatibility:
  - Works with both SQLite (test/dev) and PostgreSQL (production).
  - No pgvector, FAISS, or other vector infrastructure required.

Clean Architecture:
  - No FastAPI dependencies or HTTPExceptions.
  - Domain exceptions only.
"""

import json
from typing import List

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.exceptions import EmbeddingError
from app.repositories.chunk_repository import ChunkRepository
from app.schemas.search import SearchResultItem
from app.services.embedding_service import EmbeddingService


class SearchService:
    """Performs in-memory cosine-similarity semantic search over stored chunk embeddings."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.chunk_repo = ChunkRepository(db)
        self.embedding_svc = EmbeddingService(db)

    async def search(self, query: str, top_k: int = 5) -> List[SearchResultItem]:
        """Return the top-K most semantically similar chunks for the given query.

        Args:
            query: The user's natural-language search query.
            top_k: Number of results to return (caller is responsible for
                   validating the range; safe default is 5).

        Returns:
            List of SearchResultItem, ranked by cosine similarity descending.
            Returns an empty list when no chunks have embeddings yet.

        Raises:
            EmbeddingError: Query embedding generation failed.
        """
        # --- 1. Embed the query ---
        query_vector = await self.embedding_svc.embed_query(query)
        query_np = np.array(query_vector, dtype=np.float32)
        query_norm = np.linalg.norm(query_np)

        if query_norm == 0.0:
            logger.warning("SEARCH | Zero-norm query vector — returning no results.")
            return []

        # --- 2. Load all chunks with embeddings ---
        chunks = await self.chunk_repo.get_all_with_embeddings()
        if not chunks:
            logger.info("SEARCH | No embedded chunks found in database.")
            return []

        logger.info(f"SEARCH | Scoring {len(chunks)} embedded chunks for query")

        # --- 3. Compute cosine similarity ---
        results: List[SearchResultItem] = []
        for chunk in chunks:
            if not chunk.embedding:
                continue  # defensive: skip rows that somehow slipped through

            try:
                chunk_vector = np.array(json.loads(chunk.embedding), dtype=np.float32)
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning(
                    f"SEARCH | Skipping chunk {chunk.id} — bad embedding JSON: {exc}"
                )
                continue

            chunk_norm = np.linalg.norm(chunk_vector)
            if chunk_norm == 0.0:
                similarity = 0.0
            else:
                similarity = float(np.dot(query_np, chunk_vector) / (query_norm * chunk_norm))

            # Resolve filename from eagerly-loaded relationship
            filename: str | None = None
            if chunk.document is not None:
                filename = chunk.document.original_filename

            results.append(
                SearchResultItem(
                    document_id=chunk.document_id,
                    chunk_id=chunk.id,
                    chunk_index=chunk.chunk_index,
                    chunk_text=chunk.chunk_text,
                    similarity_score=round(similarity, 6),
                    filename=filename,
                )
            )

        # --- 4. Rank and truncate ---
        results.sort(key=lambda r: r.similarity_score, reverse=True)
        top_results = results[:top_k]

        logger.info(
            f"SEARCH | Returning {len(top_results)} / {len(results)} results "
            f"| top_k={top_k} | best_score="
            f"{top_results[0].similarity_score if top_results else 'N/A'}"
        )
        return top_results
