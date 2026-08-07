"""Backend test suite for Phase 6: Document Embeddings.

Covers:
  - EmbeddingService.embed_document: no chunks skips gracefully
  - EmbeddingService._embed_local: returns correct-shape vectors (mocked)
  - EmbeddingService.embed_document: vectors stored as JSON, model name recorded
  - EmbeddingService._embed_openai: raises EmbeddingError when API key missing
"""

import json
import uuid
from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EmbeddingError
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.repositories.chunk_repository import ChunkRepository
from app.services.embedding_service import EmbeddingService


# ---------------------------------------------------------------------------
# Helpers (reuse same pattern as test_chunking.py)
# ---------------------------------------------------------------------------

async def _make_user(db: AsyncSession) -> User:
    user = User(
        email="embed_tester@example.com",
        username="embed_tester",
        hashed_password="hashed",
        full_name="Embed Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_project(db: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(name="Embed Test Project", owner_id=owner_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def _make_document(db: AsyncSession, project_id: uuid.UUID, user_id: uuid.UUID) -> Document:
    document = Document(
        project_id=project_id,
        uploaded_by=user_id,
        original_filename="embed_test.txt",
        stored_filename=f"stored_{uuid.uuid4().hex}.txt",
        storage_path=f"projects/{project_id}/embed_test.txt",
        mime_type="text/plain",
        extension="txt",
        file_size=100,
        status=DocumentStatus.PROCESSED,
        extracted_text="Sample text for embedding.",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


async def _make_chunk(
    db: AsyncSession, document_id: uuid.UUID, index: int = 0, text: str = "chunk text"
) -> DocumentChunk:
    chunk = DocumentChunk(
        document_id=document_id,
        chunk_index=index,
        chunk_text=text,
        chunk_size=len(text),
        start_char=0,
        end_char=len(text),
    )
    db.add(chunk)
    await db.flush()
    await db.refresh(chunk)
    return chunk


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestEmbeddingServiceNoChunks:
    @pytest.mark.asyncio
    async def test_embed_document_no_chunks_returns_empty(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_document(db_session, project.id, user.id)

        svc = EmbeddingService(db_session)
        result = await svc.embed_document(document.id)
        assert result == []


class TestEmbeddingServiceLocalProvider:
    @pytest.mark.asyncio
    async def test_embed_local_stores_json_vector(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_document(db_session, project.id, user.id)
        chunk = await _make_chunk(db_session, document.id, text="hello world")

        svc = EmbeddingService(db_session)
        with patch.object(svc, "_embed_local", return_value=[[0.1, 0.2, 0.3]]):
            updated = await svc.embed_document(document.id)

        assert len(updated) == 1
        stored_vector = json.loads(updated[0].embedding)
        assert stored_vector == [0.1, 0.2, 0.3]
        assert updated[0].embedding_model is not None
        assert updated[0].embedding_generated_at is not None


    @pytest.mark.asyncio
    async def test_embed_multiple_chunks(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_document(db_session, project.id, user.id)

        for i in range(3):
            await _make_chunk(db_session, document.id, index=i, text=f"chunk number {i}")

        fake_vectors = [[float(i)] * 5 for i in range(3)]

        svc = EmbeddingService(db_session)
        with patch.object(svc, "_embed_local", return_value=fake_vectors):
            updated = await svc.embed_document(document.id)

        assert len(updated) == 3
        for i, chunk in enumerate(updated):
            assert json.loads(chunk.embedding) == fake_vectors[i]


class TestEmbeddingServiceOpenAIProvider:
    @pytest.mark.asyncio
    async def test_openai_raises_when_no_api_key(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_document(db_session, project.id, user.id)
        await _make_chunk(db_session, document.id)

        svc = EmbeddingService(db_session)

        with patch("app.core.config.settings") as mock_settings:
            mock_settings.EMBEDDING_PROVIDER = "openai"
            mock_settings.OPENAI_API_KEY = ""
            mock_settings.EMBEDDING_MODEL = "text-embedding-3-small"

            with pytest.raises(EmbeddingError, match="OPENAI_API_KEY"):
                await svc._embed_openai(["test text"])


class TestEmbeddingServiceUpdatePersistence:
    @pytest.mark.asyncio
    async def test_embedding_persisted_to_db(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_document(db_session, project.id, user.id)
        chunk = await _make_chunk(db_session, document.id, text="persist this")

        repo = ChunkRepository(db_session)
        generated_at = datetime.now(timezone.utc)
        updated = await repo.update_embedding(
            chunk=chunk,
            embedding_json="[1.0, 2.0, 3.0]",
            model_name="test-model",
            generated_at=generated_at,
        )

        assert updated.embedding == "[1.0, 2.0, 3.0]"
        assert updated.embedding_model == "test-model"
        assert updated.embedding_generated_at is not None
