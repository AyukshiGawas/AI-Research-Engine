"""Phase 8 & Phase 9 — AI Research Chat (RAG) with Citations & Sources tests.

Covers:
  Unit:
    - ChatService.answer_question() rejects empty or whitespace-only questions.
    - ChatService.answer_question() returns fallback message when no relevant chunks found.
    - ChatService.answer_question() assigns stable 1-indexed citation numbers [1], [2] to sources.
    - ChatService.answer_question() builds structured prompt with strict citation rules.
    - ChatService.answer_question() generates completion with inline citations.
    - ChatService.answer_question() raises ChatError when OPENAI_API_KEY is missing.
    - ChatService.answer_question() raises ChatError when OpenAI call fails.
    - ChatService.answer_question() propagates EmbeddingError from SearchService.

  API Endpoint:
    - POST /api/v1/chat requires authentication (401 when no token).
    - POST /api/v1/chat returns 422 for empty question.
    - POST /api/v1/chat returns 422 for whitespace-only question.
    - POST /api/v1/chat returns 422 for top_k < 1 or top_k > 50.
    - POST /api/v1/chat returns 200 with fallback answer and empty sources when no chunks indexed.
    - POST /api/v1/chat returns 200 with generated answer containing inline citations and structured sources.
    - POST /api/v1/chat verifies stable citation numbering [1], [2] and metadata consistency across multiple sources.
    - POST /api/v1/chat returns 503 when OpenAI API key is missing or OpenAI fails.
"""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ChatError, EmbeddingError
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.schemas.chat import CitationSourceItem
from app.schemas.search import SearchResultItem
from app.services.chat_service import ChatService


# ---------------------------------------------------------------------------
# Shared DB helpers
# ---------------------------------------------------------------------------


async def _make_user(db: AsyncSession, email: str = "chat_user@example.com") -> User:
    username = email.split("@")[0].replace(".", "_")
    user = User(
        email=email,
        username=username,
        hashed_password="hashed_secret",
        full_name="Chat Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_project(db: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(name="Chat Test Project", owner_id=owner_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def _make_document(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str = "chat_doc.txt",
) -> Document:
    document = Document(
        project_id=project_id,
        uploaded_by=user_id,
        original_filename=filename,
        stored_filename=f"stored_{uuid.uuid4().hex}.txt",
        storage_path=f"projects/{project_id}/{filename}",
        mime_type="text/plain",
        extension="txt",
        file_size=250,
        status=DocumentStatus.PROCESSED,
        extracted_text="Quantum computing utilizes qubits for superposition and entanglement.",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def _make_chunk(
    db: AsyncSession,
    document_id: uuid.UUID,
    index: int = 0,
    text: str = "Quantum computing utilizes qubits for superposition.",
    embedding: list | None = None,
) -> DocumentChunk:
    embedding_json = json.dumps(embedding) if embedding is not None else None
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=index,
        chunk_text=text,
        chunk_size=len(text),
        start_char=0,
        end_char=len(text),
        embedding=embedding_json,
        embedding_model="all-MiniLM-L6-v2" if embedding is not None else None,
    )
    db.add(chunk)
    await db.flush()
    await db.refresh(chunk)
    return chunk


# ---------------------------------------------------------------------------
# Unit Tests — ChatService
# ---------------------------------------------------------------------------


class TestChatServiceValidation:
    @pytest.mark.asyncio
    async def test_empty_question_raises_chat_error(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        with pytest.raises(ChatError, match="empty or whitespace"):
            await svc.answer_question("")

    @pytest.mark.asyncio
    async def test_whitespace_question_raises_chat_error(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        with pytest.raises(ChatError, match="empty or whitespace"):
            await svc.answer_question("   \n\t  ")


class TestChatServiceNoChunks:
    @pytest.mark.asyncio
    async def test_returns_fallback_when_no_sources(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        with patch.object(svc.search_svc, "search", new=AsyncMock(return_value=[])):
            answer, sources = await svc.answer_question("What is quantum computing?", top_k=5)

        assert "could not find any relevant information" in answer.lower()
        assert sources == []


class TestChatServicePromptAndCitations:
    @pytest.mark.asyncio
    async def test_build_prompt_structure_and_citation_instructions(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        sample_sources = [
            CitationSourceItem(
                citation_number=1,
                document_id=uuid.uuid4(),
                chunk_id=uuid.uuid4(),
                chunk_index=0,
                chunk_text="Qubits can exist in superposition.",
                similarity_score=0.95,
                filename="quantum_intro.pdf",
            ),
            CitationSourceItem(
                citation_number=2,
                document_id=uuid.uuid4(),
                chunk_id=uuid.uuid4(),
                chunk_index=1,
                chunk_text="Entanglement connects qubits across distances.",
                similarity_score=0.89,
                filename="quantum_entangle.pdf",
            ),
        ]
        messages = svc._build_prompt("How do qubits work?", sample_sources)
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert "Citation Rules:" in messages[0]["content"]
        assert "[1]" in messages[0]["content"]
        assert "Never invent or hallucinate citations" in messages[0]["content"]

        assert messages[1]["role"] == "user"
        assert "[1] Source: quantum_intro.pdf (Chunk 0)" in messages[1]["content"]
        assert "Qubits can exist in superposition." in messages[1]["content"]
        assert "[2] Source: quantum_entangle.pdf (Chunk 1)" in messages[1]["content"]
        assert "Entanglement connects qubits across distances." in messages[1]["content"]
        assert "Question: How do qubits work?" in messages[1]["content"]
        assert "Answer (with inline citations [1], [2], etc.):" in messages[1]["content"]

    @pytest.mark.asyncio
    async def test_answer_question_assigns_stable_citation_numbers(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        doc_id = uuid.uuid4()
        raw_results = [
            SearchResultItem(
                document_id=doc_id,
                chunk_id=uuid.uuid4(),
                chunk_index=0,
                chunk_text="First chunk text",
                similarity_score=0.95,
                filename="doc1.txt",
            ),
            SearchResultItem(
                document_id=doc_id,
                chunk_id=uuid.uuid4(),
                chunk_index=1,
                chunk_text="Second chunk text",
                similarity_score=0.85,
                filename="doc1.txt",
            ),
        ]

        mock_completion = "First statement [1]. Second statement [2]."

        with patch.object(svc.search_svc, "search", new=AsyncMock(return_value=raw_results)), \
             patch.object(svc, "_generate_completion", new=AsyncMock(return_value=mock_completion)):
            answer, sources = await svc.answer_question("Question?", top_k=2)

        assert answer == mock_completion
        assert len(sources) == 2
        assert sources[0].citation_number == 1
        assert sources[0].chunk_text == "First chunk text"
        assert sources[1].citation_number == 2
        assert sources[1].chunk_text == "Second chunk text"

    @pytest.mark.asyncio
    async def test_answer_question_successful_flow_with_citations(self, db_session: AsyncSession):
        user = await _make_user(db_session, "chat_flow@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        chunk = await _make_chunk(db_session, doc.id, 0, embedding=[1.0, 0.0])

        svc = ChatService(db_session)
        sample_results = [
            SearchResultItem(
                document_id=doc.id,
                chunk_id=chunk.id,
                chunk_index=0,
                chunk_text=chunk.chunk_text,
                similarity_score=0.92,
                filename=doc.original_filename,
            )
        ]

        mock_completion_text = "Qubits enable quantum superposition [1]."

        with patch.object(svc.search_svc, "search", new=AsyncMock(return_value=sample_results)), \
             patch.object(svc, "_generate_completion", new=AsyncMock(return_value=mock_completion_text)):
            answer, sources = await svc.answer_question("Explain qubits", top_k=3)

        assert answer == mock_completion_text
        assert len(sources) == 1
        assert sources[0].citation_number == 1
        assert sources[0].chunk_id == chunk.id
        assert sources[0].filename == doc.original_filename


class TestChatServiceErrorHandling:
    @pytest.mark.asyncio
    async def test_missing_openai_api_key_raises_chat_error(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        sample_sources = [
            SearchResultItem(
                document_id=uuid.uuid4(),
                chunk_id=uuid.uuid4(),
                chunk_index=0,
                chunk_text="Some text",
                similarity_score=0.88,
            )
        ]

        with patch.object(svc.search_svc, "search", new=AsyncMock(return_value=sample_sources)), \
             patch("app.services.chat_service.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = ""
            with pytest.raises(ChatError, match="OPENAI_API_KEY"):
                await svc.answer_question("Question")

    @pytest.mark.asyncio
    async def test_openai_api_failure_raises_chat_error(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        sample_sources = [
            SearchResultItem(
                document_id=uuid.uuid4(),
                chunk_id=uuid.uuid4(),
                chunk_index=0,
                chunk_text="Some text",
                similarity_score=0.88,
            )
        ]

        mock_openai = MagicMock()
        mock_client = MagicMock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI rate limit exceeded")
        )
        mock_openai.AsyncOpenAI.return_value = mock_client

        with patch.object(svc.search_svc, "search", new=AsyncMock(return_value=sample_sources)), \
             patch("app.services.chat_service.settings") as mock_settings, \
             patch.dict("sys.modules", {"openai": mock_openai}):
            mock_settings.OPENAI_API_KEY = "sk-fake-key"
            mock_settings.CHAT_MODEL = "gpt-4o-mini"

            with pytest.raises(ChatError, match="LLM chat completion failed"):
                await svc.answer_question("Question")

    @pytest.mark.asyncio
    async def test_embedding_error_propagates(self, db_session: AsyncSession):
        svc = ChatService(db_session)
        with patch.object(svc.search_svc, "search", new=AsyncMock(side_effect=EmbeddingError("Model offline"))):
            with pytest.raises(EmbeddingError, match="Model offline"):
                await svc.answer_question("Question")


# ---------------------------------------------------------------------------
# API Endpoint Tests — POST /api/v1/chat
# ---------------------------------------------------------------------------


class TestChatEndpointAuth:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/chat", json={"question": "What is AI?", "top_k": 5}
        )
        assert response.status_code == 401


class TestChatEndpointValidation:
    @pytest.mark.asyncio
    async def test_empty_question_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_chat1@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/chat", json={"question": "", "top_k": 5}
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_whitespace_question_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_chat2@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/chat", json={"question": "   \n\t ", "top_k": 5}
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_top_k_invalid_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_chat3@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            res_zero = await client.post(
                "/api/v1/chat", json={"question": "Valid question?", "top_k": 0}
            )
            assert res_zero.status_code == 422

            res_max = await client.post(
                "/api/v1/chat", json={"question": "Valid question?", "top_k": 51}
            )
            assert res_max.status_code == 422
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)


class TestChatEndpointExecution:
    @pytest.mark.asyncio
    async def test_chat_returns_fallback_when_no_indexed_chunks(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "chat_empty@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            with patch(
                "app.services.search_service.EmbeddingService.embed_query",
                new_callable=AsyncMock,
                return_value=[1.0, 0.0],
            ):
                response = await client.post(
                    "/api/v1/chat", json={"question": "What is relativity?", "top_k": 5}
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "What is relativity?"
        assert "could not find any relevant information" in data["answer"].lower()
        assert data["sources"] == []

    @pytest.mark.asyncio
    async def test_chat_returns_answer_with_citations_and_structured_sources(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "chat_success@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id, filename="quantum.txt")
        chunk = await _make_chunk(
            db_session,
            doc.id,
            0,
            text="Quantum teleportation transmits qubit states.",
            embedding=[1.0, 0.0],
        )

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        mock_choice = MagicMock()
        mock_choice.message.content = "Quantum teleportation is the transmission of qubit states [1]."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.AsyncOpenAI.return_value = mock_client_instance

        try:
            with patch(
                "app.services.search_service.EmbeddingService.embed_query",
                new_callable=AsyncMock,
                return_value=[1.0, 0.0],
            ), patch("app.services.chat_service.settings") as mock_settings, \
               patch.dict("sys.modules", {"openai": mock_openai}):
                mock_settings.OPENAI_API_KEY = "sk-test-key-12345"
                mock_settings.CHAT_MODEL = "gpt-4o-mini"

                response = await client.post(
                    "/api/v1/chat",
                    json={"question": "What is quantum teleportation?", "top_k": 3},
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["question"] == "What is quantum teleportation?"
        assert data["answer"] == "Quantum teleportation is the transmission of qubit states [1]."
        assert len(data["sources"]) == 1
        src = data["sources"][0]
        assert src["citation_number"] == 1
        assert src["document_id"] == str(doc.id)
        assert src["chunk_id"] == str(chunk.id)
        assert src["chunk_index"] == 0
        assert src["filename"] == "quantum.txt"
        assert src["chunk_text"] == "Quantum teleportation transmits qubit states."
        assert src["similarity_score"] > 0.9

    @pytest.mark.asyncio
    async def test_chat_multiple_sources_citation_consistency(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "chat_multi@example.com")
        project = await _make_project(db_session, user.id)
        doc1 = await _make_document(db_session, project.id, user.id, filename="doc_a.txt")
        chunk1 = await _make_chunk(db_session, doc1.id, 0, text="First topic text.", embedding=[1.0, 0.0])
        chunk2 = await _make_chunk(db_session, doc1.id, 1, text="Second topic text.", embedding=[0.8, 0.6])

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        mock_choice = MagicMock()
        mock_choice.message.content = "According to source [1], first topic holds. Source [2] confirms second topic."
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]

        mock_openai = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_response)
        mock_openai.AsyncOpenAI.return_value = mock_client_instance

        try:
            with patch(
                "app.services.search_service.EmbeddingService.embed_query",
                new_callable=AsyncMock,
                return_value=[1.0, 0.0],
            ), patch("app.services.chat_service.settings") as mock_settings, \
               patch.dict("sys.modules", {"openai": mock_openai}):
                mock_settings.OPENAI_API_KEY = "sk-test-key-12345"
                mock_settings.CHAT_MODEL = "gpt-4o-mini"

                response = await client.post(
                    "/api/v1/chat",
                    json={"question": "Compare topics", "top_k": 2},
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data["sources"]) == 2
        assert data["sources"][0]["citation_number"] == 1
        assert data["sources"][1]["citation_number"] == 2
        assert data["sources"][0]["chunk_id"] == str(chunk1.id)
        assert data["sources"][1]["chunk_id"] == str(chunk2.id)

    @pytest.mark.asyncio
    async def test_chat_missing_api_key_returns_503(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "chat_nokey@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        await _make_chunk(db_session, doc.id, 0, embedding=[1.0, 0.0])

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with patch(
                "app.services.search_service.EmbeddingService.embed_query",
                new_callable=AsyncMock,
                return_value=[1.0, 0.0],
            ), patch("app.services.chat_service.settings") as mock_settings:
                mock_settings.OPENAI_API_KEY = ""
                response = await client.post(
                    "/api/v1/chat",
                    json={"question": "Explain quantum states?", "top_k": 5},
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 503
        assert "OPENAI_API_KEY" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chat_openai_failure_returns_503(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "chat_err@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        await _make_chunk(db_session, doc.id, 0, embedding=[1.0, 0.0])

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        mock_openai = MagicMock()
        mock_client_instance = MagicMock()
        mock_client_instance.chat.completions.create = AsyncMock(
            side_effect=Exception("OpenAI API unreachable")
        )
        mock_openai.AsyncOpenAI.return_value = mock_client_instance

        try:
            with patch(
                "app.services.search_service.EmbeddingService.embed_query",
                new_callable=AsyncMock,
                return_value=[1.0, 0.0],
            ), patch("app.services.chat_service.settings") as mock_settings, \
               patch.dict("sys.modules", {"openai": mock_openai}):
                mock_settings.OPENAI_API_KEY = "sk-valid-key"
                mock_settings.CHAT_MODEL = "gpt-4o-mini"

                response = await client.post(
                    "/api/v1/chat",
                    json={"question": "Explain quantum states?", "top_k": 5},
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 503
        assert "LLM chat completion failed" in response.json()["detail"]
