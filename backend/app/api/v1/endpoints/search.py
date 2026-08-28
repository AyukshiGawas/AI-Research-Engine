"""Semantic search API endpoint — Phase 7.

POST /api/v1/search

Accepts a JSON body with ``query`` and optional ``top_k`` and returns the
top-K most relevant document chunks ranked by cosine similarity.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.exceptions import EmbeddingError
from app.models.user import User
from app.schemas.search import SearchRequest, SearchResponse
from app.services.search_service import SearchService

router = APIRouter()


@router.post(
    "/search",
    response_model=SearchResponse,
    summary="Semantic search over all indexed document chunks",
    tags=["search"],
)
async def semantic_search(
    body: SearchRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    """Return the top-K document chunks most semantically similar to the query.

    - **query**: Natural-language search text (1–2000 characters).
    - **top_k**: Maximum results to return (1–50, default 5).

    Cosine similarity is computed in memory against all stored chunk embeddings.
    No vector database infrastructure is required.

    Raises **422** for validation errors (empty query, out-of-range top_k).
    Raises **503** if the embedding model is unavailable.
    """
    svc = SearchService(db)
    try:
        results = await svc.search(query=body.query, top_k=body.top_k)
    except EmbeddingError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding model unavailable: {exc}",
        ) from exc

    return SearchResponse(
        query=body.query,
        total_results=len(results),
        results=results,
    )
