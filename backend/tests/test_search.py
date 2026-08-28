"""Phase 7 — Semantic Search tests.

Covers:
  Unit:
    - SearchService.search() returns empty list when no embedded chunks exist.
    - SearchService.search() ranks results by cosine similarity descending.
    - SearchService.search() honours top_k limit.
    - SearchService.search() skips chunks with NULL embeddings.
    - EmbeddingService.embed_query() delegates to _embed_local for local provider.

  API:
    - POST /api/v1/search requires authentication (401 when no token).
    - POST /api/v1/search returns 422 for empty query string.
    - POST /api/v1/search returns 422 for top_k = 0.
    - POST /api/v1/search returns 422 for top_k > 50.
    - POST /api/v1/search returns 200 with ranked results for valid request.
    - POST /api/v1/search returns empty results list when no embeddings exist.
"""

import json
import uuid
from unittest.mock import AsyncMock, patch

import numpy as np
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EmbeddingError
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService


# ---------------------------------------------------------------------------
# Shared DB helpers (match pattern used by test_embeddings.py)
# ---------------------------------------------------------------------------


async def _make_user(db: AsyncSession, email: str = "search_user@example.com") -> User:
    username = email.split("@")[0].replace(".", "_")
    user = User(
        email=email,
        username=username,
        hashed_password="hashed",
        full_name="Search Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_project(db: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(name="Search Test Project", owner_id=owner_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def _make_document(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    filename: str = "search_doc.txt",
) -> Document:
    document = Document(
        project_id=project_id,
        uploaded_by=user_id,
        original_filename=filename,
        stored_filename=f"stored_{uuid.uuid4().hex}.txt",
        storage_path=f"projects/{project_id}/{filename}",
        mime_type="text/plain",
        extension="txt",
        file_size=200,
        status=DocumentStatus.PROCESSED,
        extracted_text="Sample text for search testing.",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def _make_chunk(
    db: AsyncSession,
    document_id: uuid.UUID,
    index: int = 0,
    text: str = "sample chunk text",
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
# Unit Tests — ChunkRepository.get_all_with_embeddings
# ---------------------------------------------------------------------------


class TestChunkRepositoryGetAllWithEmbeddings:
    @pytest.mark.asyncio
    async def test_returns_only_embedded_chunks(self, db_session: AsyncSession):
        user = await _make_user(db_session, "repo_test@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)

        embedded = await _make_chunk(db_session, doc.id, 0, embedding=[0.1, 0.2, 0.3])
        _no_embed = await _make_chunk(db_session, doc.id, 1, embedding=None)

        repo = ChunkRepository(db_session)
        results = await repo.get_all_with_embeddings()

        ids = [c.id for c in results]
        assert embedded.id in ids
        assert _no_embed.id not in ids

    @pytest.mark.asyncio
    async def test_empty_when_no_embeddings(self, db_session: AsyncSession):
        user = await _make_user(db_session, "repo_empty@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        await _make_chunk(db_session, doc.id, 0, embedding=None)

        repo = ChunkRepository(db_session)
        results = await repo.get_all_with_embeddings()
        assert results == []


# ---------------------------------------------------------------------------
# Unit Tests — EmbeddingService.embed_query
# ---------------------------------------------------------------------------


class TestEmbedQuery:
    @pytest.mark.asyncio
    async def test_embed_query_returns_vector(self, db_session: AsyncSession):
        svc = EmbeddingService(db_session)
        fake_vector = [0.1, 0.2, 0.3]
        with patch.object(svc, "_embed_local", return_value=[fake_vector]):
            result = await svc.embed_query("test query")
        assert result == fake_vector

    @pytest.mark.asyncio
    async def test_embed_query_propagates_error(self, db_session: AsyncSession):
        svc = EmbeddingService(db_session)
        with patch.object(svc, "_embed_local", side_effect=RuntimeError("model error")):
            with pytest.raises(EmbeddingError, match="Query embedding generation failed"):
                await svc.embed_query("test query")


# ---------------------------------------------------------------------------
# Unit Tests — SearchService
# ---------------------------------------------------------------------------


class TestSearchServiceNoChunks:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_embedded_chunks(self, db_session: AsyncSession):
        user = await _make_user(db_session, "no_chunks@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        # chunk with NO embedding
        await _make_chunk(db_session, doc.id, embedding=None)

        svc = SearchService(db_session)
        with patch.object(svc.embedding_svc, "embed_query", new=AsyncMock(return_value=[1.0, 0.0])):
            results = await svc.search("anything", top_k=5)

        assert results == []


class TestSearchServiceRanking:
    @pytest.mark.asyncio
    async def test_results_ranked_by_similarity_descending(self, db_session: AsyncSession):
        """Chunks with higher cosine similarity to the query appear first."""
        user = await _make_user(db_session, "ranking@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)

        # query vector = [1, 0]
        # chunk A: [1, 0]  -> similarity 1.0  (most similar)
        # chunk B: [0, 1]  -> similarity 0.0  (orthogonal)
        # chunk C: [0.7071, 0.7071] -> similarity ~0.707
        await _make_chunk(db_session, doc.id, 0, "chunk A", embedding=[1.0, 0.0])
        await _make_chunk(db_session, doc.id, 1, "chunk B", embedding=[0.0, 1.0])
        await _make_chunk(db_session, doc.id, 2, "chunk C", embedding=[0.7071, 0.7071])

        svc = SearchService(db_session)
        with patch.object(svc.embedding_svc, "embed_query", new=AsyncMock(return_value=[1.0, 0.0])):
            results = await svc.search("query", top_k=10)

        assert len(results) == 3
        assert results[0].chunk_text == "chunk A"
        assert results[0].similarity_score > results[1].similarity_score
        assert results[1].similarity_score > results[2].similarity_score

    @pytest.mark.asyncio
    async def test_top_k_limits_results(self, db_session: AsyncSession):
        user = await _make_user(db_session, "topk@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)

        for i in range(5):
            await _make_chunk(
                db_session, doc.id, i, f"chunk {i}",
                embedding=[float(i) / 5.0, 1.0 - float(i) / 5.0],
            )

        svc = SearchService(db_session)
        with patch.object(svc.embedding_svc, "embed_query", new=AsyncMock(return_value=[1.0, 0.0])):
            results = await svc.search("query", top_k=2)

        assert len(results) == 2

    @pytest.mark.asyncio
    async def test_filename_included_in_results(self, db_session: AsyncSession):
        user = await _make_user(db_session, "filename@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(
            db_session, project.id, user.id, filename="important_paper.pdf"
        )
        await _make_chunk(db_session, doc.id, 0, embedding=[1.0, 0.0])

        svc = SearchService(db_session)
        with patch.object(svc.embedding_svc, "embed_query", new=AsyncMock(return_value=[1.0, 0.0])):
            results = await svc.search("query", top_k=5)

        assert len(results) == 1
        assert results[0].filename == "important_paper.pdf"
        assert results[0].document_id == doc.id


class TestSearchServiceFieldsPresent:
    @pytest.mark.asyncio
    async def test_result_contains_all_required_fields(self, db_session: AsyncSession):
        user = await _make_user(db_session, "fields@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)
        chunk = await _make_chunk(db_session, doc.id, 0, "hello world", embedding=[1.0])

        svc = SearchService(db_session)
        with patch.object(svc.embedding_svc, "embed_query", new=AsyncMock(return_value=[1.0])):
            results = await svc.search("hello", top_k=1)

        assert len(results) == 1
        r = results[0]
        assert r.document_id == doc.id
        assert r.chunk_id == chunk.id
        assert r.chunk_index == 0
        assert r.chunk_text == "hello world"
        assert isinstance(r.similarity_score, float)


# ---------------------------------------------------------------------------
# API Endpoint Tests — POST /api/v1/search
# ---------------------------------------------------------------------------


class TestSearchEndpointAuth:
    @pytest.mark.asyncio
    async def test_unauthenticated_returns_401(self, client: AsyncClient):
        response = await client.post(
            "/api/v1/search", json={"query": "test", "top_k": 5}
        )
        assert response.status_code == 401


class TestSearchEndpointValidation:
    @pytest.mark.asyncio
    async def test_empty_query_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_test@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/search", json={"query": "", "top_k": 5}
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_top_k_zero_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_zero@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/search", json={"query": "hello", "top_k": 0}
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_top_k_over_max_returns_422(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "val_max@example.com")
        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user
        try:
            response = await client.post(
                "/api/v1/search", json={"query": "hello", "top_k": 51}
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)
        assert response.status_code == 422


class TestSearchEndpointResults:
    @pytest.mark.asyncio
    async def test_returns_empty_results_when_no_embeddings(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "empty_res@example.com")
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
                    "/api/v1/search", json={"query": "anything", "top_k": 5}
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["results"] == []
        assert data["total_results"] == 0
        assert data["query"] == "anything"

    @pytest.mark.asyncio
    async def test_returns_ranked_results(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "ranked@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id, "ranked_doc.txt")

        await _make_chunk(db_session, doc.id, 0, "most relevant", embedding=[1.0, 0.0])
        await _make_chunk(db_session, doc.id, 1, "least relevant", embedding=[0.0, 1.0])

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
                    "/api/v1/search", json={"query": "relevant", "top_k": 5}
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["total_results"] == 2
        assert len(data["results"]) == 2

        # First result should be the most similar
        assert data["results"][0]["chunk_text"] == "most relevant"
        assert data["results"][0]["similarity_score"] > data["results"][1]["similarity_score"]

        # All required fields present
        first = data["results"][0]
        assert "document_id" in first
        assert "chunk_id" in first
        assert "chunk_index" in first
        assert "chunk_text" in first
        assert "similarity_score" in first
        assert first["filename"] == "ranked_doc.txt"

    @pytest.mark.asyncio
    async def test_top_k_respected_in_response(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "topk_api@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_document(db_session, project.id, user.id)

        for i in range(5):
            await _make_chunk(
                db_session, doc.id, i,
                embedding=[float(i + 1), 0.0],
            )

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
                    "/api/v1/search", json={"query": "test", "top_k": 3}
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert len(data["results"]) == 3
