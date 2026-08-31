"""Pydantic schemas for Phase 8 & Phase 9: AI Research Chat (RAG) with Citations."""

import uuid
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class ChatRequest(BaseModel):
    """Request body for the RAG chat endpoint."""

    question: str = Field(
        ...,
        min_length=1,
        max_length=2000,
        description="Natural-language question from the user.",
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Maximum number of context chunks to retrieve for RAG (1–50, default 5).",
    )

    @field_validator("question")
    @classmethod
    def question_must_not_be_blank(cls, v: str) -> str:
        """Ensure question contains non-whitespace characters."""
        if not v.strip():
            raise ValueError("Question cannot be empty or whitespace-only.")
        return v.strip()


class CitationSourceItem(BaseModel):
    """Structured citation source chunk item for RAG chat responses."""

    citation_number: int = Field(
        ...,
        ge=1,
        description="Stable 1-indexed citation number used for inline citations [1], [2], etc.",
    )
    document_id: uuid.UUID
    chunk_id: uuid.UUID
    chunk_index: int
    chunk_text: str
    similarity_score: float
    filename: Optional[str] = None


class ChatResponse(BaseModel):
    """Response returned by the RAG chat endpoint with inline citations and sources."""

    question: str
    answer: str
    sources: List[CitationSourceItem]
