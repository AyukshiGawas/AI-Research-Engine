"""AI Research Chat (RAG) API endpoint — Phase 8.

POST /api/v1/chat

Accepts a JSON body with ``question`` and optional ``top_k``, retrieves relevant
chunks using Phase 7 semantic search, queries OpenAI LLM, and returns the generated
answer along with the source chunks.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies.auth import get_current_active_user
from app.exceptions import ChatError, EmbeddingError
from app.models.user import User
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter()


@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Ask a question against indexed research documents (RAG)",
    tags=["chat"],
)
async def chat_rag(
    body: ChatRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """Answer a user question using RAG over stored document chunk embeddings.

    - **question**: Natural-language question (1–2000 characters).
    - **top_k**: Maximum number of context chunks to retrieve (1–50, default 5).

    Retrieves top relevant chunks using semantic search, constructs a prompt,
    and calls OpenAI Chat Completions API.

    Raises **401** if not authenticated.
    Raises **422** for validation errors (empty question, invalid top_k).
    Raises **503** if OpenAI or the embedding model is unavailable or misconfigured.
    """
    svc = ChatService(db)
    try:
        answer, sources = await svc.answer_question(
            question=body.question, top_k=body.top_k
        )
    except (EmbeddingError, ChatError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return ChatResponse(
        question=body.question,
        answer=answer,
        sources=sources,
    )
