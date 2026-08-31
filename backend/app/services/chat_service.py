"""Chat service — Phase 8: AI Research Chat (RAG).

Responsibilities:
  1. Retrieve relevant DocumentChunk context for the user's question via SearchService.
  2. Assemble a RAG prompt incorporating retrieved chunk text and source metadata.
  3. Call the OpenAI Chat Completions API with the assembled context.
  4. Return the generated answer alongside the retrieved source chunks.
  5. Handle edge cases cleanly:
     - Empty question or whitespace: raises ChatError.
     - No relevant chunks: returns a clear fallback response and empty sources list.
     - Missing OpenAI API key: raises ChatError.
     - OpenAI API failures / exceptions: raises ChatError.

Clean Architecture:
  - No FastAPI dependencies or HTTPExceptions.
  - Domain exceptions only (ChatError, EmbeddingError).
"""

from typing import List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.exceptions import ChatError, EmbeddingError
from app.schemas.search import SearchResultItem
from app.services.search_service import SearchService


class ChatService:
    """Orchestrates Retrieval-Augmented Generation (RAG) chat."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_svc = SearchService(db)

    async def answer_question(
        self, question: str, top_k: int = 5
    ) -> Tuple[str, List[SearchResultItem]]:
        """Answer a user's question using semantic search retrieval and OpenAI chat.

        Args:
            question: The user's natural-language question.
            top_k: Number of relevant chunks to retrieve for context.

        Returns:
            Tuple of (answer_text, sources_list).

        Raises:
            EmbeddingError: If semantic search embedding fails.
            ChatError: If OpenAI API key is missing or chat completion fails.
        """
        clean_question = question.strip() if question else ""
        if not clean_question:
            raise ChatError("Question cannot be empty or whitespace-only.")

        # 1. Retrieve top-K relevant chunks via SearchService
        sources = await self.search_svc.search(query=clean_question, top_k=top_k)

        # 2. Handle case where no chunks exist or were retrieved
        if not sources:
            logger.info("CHAT | No relevant chunks found for question.")
            return (
                "I could not find any relevant information in the uploaded research documents to answer your question.",
                [],
            )

        # 3. Build RAG prompt
        messages = self._build_prompt(clean_question, sources)

        # 4. Generate answer via OpenAI Chat Completions
        answer = await self._generate_completion(messages)

        logger.info(
            f"CHAT | Generated answer for question | sources_count={len(sources)}"
        )
        return answer, sources

    def _build_prompt(
        self, question: str, sources: List[SearchResultItem]
    ) -> List[dict]:
        """Construct system and user messages for the LLM chat completion."""
        system_content = (
            "You are an AI research assistant. Answer the user's question accurately, "
            "objectively, and concisely based strictly on the provided research context chunks. "
            "If the provided context does not contain sufficient information to answer the question, "
            "explicitly state that you do not have enough information from the documents."
        )

        context_blocks = []
        for idx, item in enumerate(sources, start=1):
            doc_label = item.filename or str(item.document_id)
            context_blocks.append(
                f"[Source {idx}: {doc_label} (Chunk {item.chunk_index})]\n{item.chunk_text}"
            )

        context_text = "\n\n".join(context_blocks)
        user_content = f"Context:\n{context_text}\n\nQuestion: {question}\n\nAnswer:"

        return [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content},
        ]

    async def _generate_completion(self, messages: List[dict]) -> str:
        """Call OpenAI Chat Completion API."""
        if not settings.OPENAI_API_KEY:
            raise ChatError("OPENAI_API_KEY must be set for RAG chat completion.")

        try:
            from openai import AsyncOpenAI  # type: ignore
        except ImportError as exc:
            raise ChatError(
                "openai package is not installed. Run: pip install openai"
            ) from exc

        try:
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            response = await client.chat.completions.create(
                model=settings.CHAT_MODEL,
                messages=messages,
                temperature=0.2,
            )
            content = response.choices[0].message.content
            return content.strip() if content else ""
        except Exception as exc:
            logger.error(f"CHAT | OpenAI Chat Completion error: {exc}")
            raise ChatError(f"LLM chat completion failed: {exc}") from exc
