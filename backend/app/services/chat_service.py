"""Chat service — Phase 8 & Phase 9: AI Research Chat (RAG) with Citations & Sources.

Responsibilities:
  1. Retrieve relevant DocumentChunk context for the user's question via SearchService.
  2. Map retrieved chunks to structured CitationSourceItem objects with stable 1-indexed citation numbers ([1], [2], ...).
  3. Assemble a RAG prompt instructing the LLM to ground all factual claims strictly in the numbered context sources.
  4. Call the OpenAI Chat Completions API with the assembled context.
  5. Return the generated answer (with inline citations) alongside the structured sources list.
  6. Handle edge cases cleanly:
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
from app.schemas.chat import CitationSourceItem
from app.services.search_service import SearchService


class ChatService:
    """Orchestrates Retrieval-Augmented Generation (RAG) chat with citations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.search_svc = SearchService(db)

    async def answer_question(
        self, question: str, top_k: int = 5
    ) -> Tuple[str, List[CitationSourceItem]]:
        """Answer a user's question using semantic search retrieval and OpenAI chat with citations.

        Args:
            question: The user's natural-language question.
            top_k: Number of relevant chunks to retrieve for context.

        Returns:
            Tuple of (answer_text_with_citations, structured_sources_list).

        Raises:
            EmbeddingError: If semantic search embedding fails.
            ChatError: If OpenAI API key is missing or chat completion fails.
        """
        clean_question = question.strip() if question else ""
        if not clean_question:
            raise ChatError("Question cannot be empty or whitespace-only.")

        # 1. Retrieve top-K relevant chunks via SearchService
        raw_sources = await self.search_svc.search(query=clean_question, top_k=top_k)

        # 2. Handle case where no chunks exist or were retrieved
        if not raw_sources:
            logger.info("CHAT | No relevant chunks found for question.")
            return (
                "I could not find any relevant information in the uploaded research documents to answer your question.",
                [],
            )

        # 3. Assign stable 1-indexed citation numbers to retrieved sources
        sources: List[CitationSourceItem] = [
            CitationSourceItem(
                citation_number=idx,
                document_id=item.document_id,
                chunk_id=item.chunk_id,
                chunk_index=item.chunk_index,
                chunk_text=item.chunk_text,
                similarity_score=item.similarity_score,
                filename=item.filename,
            )
            for idx, item in enumerate(raw_sources, start=1)
        ]

        # 4. Build RAG prompt with explicit citation instructions
        messages = self._build_prompt(clean_question, sources)

        # 5. Generate answer via OpenAI Chat Completions
        answer = await self._generate_completion(messages)

        logger.info(
            f"CHAT | Generated answer with citations for question | sources_count={len(sources)}"
        )
        return answer, sources

    def _build_prompt(
        self, question: str, sources: List[CitationSourceItem]
    ) -> List[dict]:
        """Construct system and user messages for the LLM chat completion with citation instructions."""
        system_content = (
            "You are an AI research assistant. Answer the user's question accurately, "
            "objectively, and concisely based strictly on the provided research context chunks.\n\n"
            "Citation Rules:\n"
            "1. Every factual statement and claim must be backed by one or more citations referring to the context chunks.\n"
            "2. Use bracketed citation numbers like [1], [2], or [1][2] corresponding to the numbered context sources.\n"
            "3. Only cite sources that are actually provided in the context. Never invent or hallucinate citations or source information.\n"
            "4. If the provided context does not contain sufficient information to answer the question, "
            "explicitly state that you do not have enough information from the documents."
        )

        context_blocks = []
        for item in sources:
            doc_label = item.filename or str(item.document_id)
            context_blocks.append(
                f"[{item.citation_number}] Source: {doc_label} (Chunk {item.chunk_index})\n{item.chunk_text}"
            )

        context_text = "\n\n".join(context_blocks)
        user_content = (
            f"Context:\n{context_text}\n\n"
            f"Question: {question}\n\n"
            "Answer (with inline citations [1], [2], etc.):"
        )

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
