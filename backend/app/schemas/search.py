"""Pydantic schemas for Phase 7: Semantic Search request and responses."""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Request body for the semantic search endpoint."""

    query: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language search query to embed and match against stored chunks.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of results to return (1–50, default 5).",
    )


class SearchResultItem(BaseModel):
    """Single ranked result returned by the semantic search endpoint."""

    document_id: uuid.UUID
    chunk_id: uuid.UUID
    chunk_index: int
    chunk_text: str
    similarity_score: float
    filename: Optional[str] = None


class SearchResponse(BaseModel):
    """Top-K semantically similar chunks for the given query."""

    query: str
    total_results: int
    results: List[SearchResultItem]
