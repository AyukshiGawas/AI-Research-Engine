"""Backend API test suite for Phase 5 & 6 endpoints.

Covers:
  - GET /{project_id}/documents/{document_id}/chunks (List chunks)
  - POST /{project_id}/documents/{document_id}/chunk (Re-trigger chunking + embedding)
"""

import uuid
from unittest.mock import patch
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_user(db: AsyncSession, email: str = "chunk_api_user@example.com") -> User:
    username = email.split("@")[0]
    user = User(
        email=email,
        username=username,
        hashed_password="hashed_password_123",
        full_name="Chunk API User",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_project(db: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(name="Chunk API Project", owner_id=owner_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def _make_processed_document(
    db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID
) -> Document:
    doc = Document(
        project_id=project_id,
        uploaded_by=user_id,
        original_filename="api_test_doc.txt",
        stored_filename=f"stored_{uuid.uuid4().hex}.txt",
        storage_path=f"projects/{project_id}/api_test_doc.txt",
        mime_type="text/plain",
        extension="txt",
        file_size=120,
        status=DocumentStatus.PROCESSED,
        extracted_text="First sentence for testing chunks API. Second sentence for testing chunks API.",
        word_count=12,
        page_count=1,
    )
    db.add(doc)
    await db.flush()
    await db.refresh(doc)
    return doc


async def _make_chunk(
    db: AsyncSession, document_id: uuid.UUID, index: int = 0
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=index,
        chunk_text="First sentence for testing chunks API.",
        chunk_size=38,
        start_char=0,
        end_char=38,
        embedding="[0.1, 0.2, 0.3]",
        embedding_model="all-MiniLM-L6-v2",
    )
    db.add(chunk)
    await db.flush()
    await db.refresh(chunk)
    return chunk


# ---------------------------------------------------------------------------
# API Endpoint Tests
# ---------------------------------------------------------------------------

class TestChunkApiEndpoints:
    @pytest.mark.asyncio
    async def test_list_chunks_unauthenticated(self, client: AsyncClient):
        p_id = uuid.uuid4()
        d_id = uuid.uuid4()
        response = await client.get(f"/api/v1/projects/{p_id}/documents/{d_id}/chunks")
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_list_chunks_success(self, client: AsyncClient, db_session: AsyncSession):
        user = await _make_user(db_session, "list_chunks@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_processed_document(db_session, project.id, user.id)
        chunk = await _make_chunk(db_session, doc.id, 0)

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            response = await client.get(
                f"/api/v1/projects/{project.id}/documents/{doc.id}/chunks"
            )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == str(doc.id)
        assert data["total_chunks"] == 1
        assert len(data["chunks"]) == 1
        assert data["chunks"][0]["id"] == str(chunk.id)
        assert data["chunks"][0]["chunk_text"] == chunk.chunk_text
        assert data["chunks"][0]["embedding_model"] == "all-MiniLM-L6-v2"

    @pytest.mark.asyncio
    async def test_rechunk_document_success(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = await _make_user(db_session, "rechunk_doc@example.com")
        project = await _make_project(db_session, user.id)
        doc = await _make_processed_document(db_session, project.id, user.id)

        from app.dependencies.auth import get_current_active_user
        from app.main import app
        app.dependency_overrides[get_current_active_user] = lambda: user

        try:
            with patch("app.services.embedding_service.EmbeddingService._embed_local", return_value=[[0.1, 0.2, 0.3]]):
                response = await client.post(
                    f"/api/v1/projects/{project.id}/documents/{doc.id}/chunk"
                )
        finally:
            app.dependency_overrides.pop(get_current_active_user, None)

        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == str(doc.id)
        assert data["total_chunks"] > 0
        assert len(data["chunks"]) == data["total_chunks"]

