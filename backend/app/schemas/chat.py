"""Pydantic schemas for Phase 8: AI Research Chat (RAG)."""

from typing import List

from pydantic import BaseModel, Field, field_validator

from app.schemas.search import SearchResultItem


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


class ChatResponse(BaseModel):
    """Response returned by the RAG chat endpoint."""

    question: str
    answer: str
    sources: List[SearchResultItem]
