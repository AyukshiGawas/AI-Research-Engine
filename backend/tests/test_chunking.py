"""Backend test suite for Phase 5: Document Chunking.

Covers:
  - ChunkingService._split_text: boundary alignment, overlap, single/empty text
  - ChunkingService.chunk_document: status guard, no-text guard, DB persistence
  - ChunkRepository: create_bulk, get_by_document, delete_by_document, count_by_document
  - Idempotent re-chunking (existing chunks replaced)
"""

import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import ChunkingError, DocumentNotFoundError, DocumentProcessingError
from app.models.document import Document, DocumentStatus
from app.models.document_chunk import DocumentChunk
from app.models.project import Project
from app.models.user import User
from app.repositories.chunk_repository import ChunkRepository
from app.services.chunking_service import ChunkingService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _make_user(db: AsyncSession) -> User:
    user = User(
        email="chunk_tester@example.com",
        username="chunk_tester",
        hashed_password="hashed",
        full_name="Chunk Tester",
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def _make_project(db: AsyncSession, owner_id: uuid.UUID) -> Project:
    project = Project(name="Chunk Test Project", owner_id=owner_id)
    db.add(project)
    await db.flush()
    await db.refresh(project)
    return project


async def _make_processed_document(
    db: AsyncSession,
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    extracted_text: str = "This is a sample extracted text for chunking.",
) -> Document:
    document = Document(
        project_id=project_id,
        uploaded_by=user_id,
        original_filename="test_chunk.txt",
        stored_filename=f"stored_{uuid.uuid4().hex}.txt",
        storage_path=f"projects/{project_id}/stored_test.txt",
        mime_type="text/plain",
        extension="txt",
        file_size=len(extracted_text.encode()),
        status=DocumentStatus.PROCESSED,
        extracted_text=extracted_text,
        word_count=len(extracted_text.split()),
        page_count=1,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)
    return document


# ---------------------------------------------------------------------------
# Unit tests — _split_text
# ---------------------------------------------------------------------------

class TestSplitText:
    def test_empty_text_returns_empty_list(self):
        result = ChunkingService._split_text("", chunk_size=100, overlap=20)
        assert result == []

    def test_short_text_single_chunk(self):
        text = "Hello world."
        result = ChunkingService._split_text(text, chunk_size=100, overlap=20)
        assert len(result) == 1
        assert result[0][0] == text.strip()
        assert result[0][1] == 0

    def test_multiple_chunks_with_overlap(self):
        # 200 chars + overlap = multiple chunks
        text = "word " * 60  # 300 chars
        result = ChunkingService._split_text(text, chunk_size=100, overlap=20)
        assert len(result) > 1
        # Each chunk should not exceed chunk_size + a small tolerance for boundary
        for chunk_text, start, end in result:
            assert len(chunk_text) <= 120  # some boundary flexibility

    def test_start_end_positions_are_correct(self):
        text = "a" * 50 + " " + "b" * 50
        result = ChunkingService._split_text(text, chunk_size=60, overlap=10)
        for chunk_text, start, end in result:
            assert start >= 0
            assert end > start
            assert end <= len(text)

    def test_no_zero_size_chunk(self):
        text = "word " * 20
        result = ChunkingService._split_text(text, chunk_size=50, overlap=10)
        for chunk_text, start, end in result:
            assert len(chunk_text) > 0

    def test_zero_chunk_size_returns_empty(self):
        result = ChunkingService._split_text("some text", chunk_size=0, overlap=0)
        assert result == []


# ---------------------------------------------------------------------------
# Integration tests — ChunkingService with DB
# ---------------------------------------------------------------------------

class TestChunkingServiceIntegration:
    @pytest.mark.asyncio
    async def test_chunk_document_creates_chunks(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_processed_document(
            db_session,
            project.id,
            user.id,
            "The quick brown fox jumps over the lazy dog. " * 30,
        )

        svc = ChunkingService(db_session)
        chunks = await svc.chunk_document(document.id)

        assert len(chunks) > 0
        for i, chunk in enumerate(chunks):
            assert chunk.document_id == document.id
            assert chunk.chunk_index == i
            assert len(chunk.chunk_text) > 0
            assert chunk.start_char >= 0
            assert chunk.end_char > chunk.start_char

    @pytest.mark.asyncio
    async def test_chunk_document_not_found(self, db_session: AsyncSession):
        svc = ChunkingService(db_session)
        with pytest.raises(DocumentNotFoundError):
            await svc.chunk_document(uuid.uuid4())

    @pytest.mark.asyncio
    async def test_chunk_document_not_processed_raises(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = Document(
            project_id=project.id,
            uploaded_by=user.id,
            original_filename="pending.txt",
            stored_filename=f"stored_{uuid.uuid4().hex}.txt",
            storage_path=f"projects/{project.id}/pending.txt",
            mime_type="text/plain",
            extension="txt",
            file_size=100,
            status=DocumentStatus.UPLOADED,
        )
        db_session.add(document)
        await db_session.flush()
        await db_session.refresh(document)

        svc = ChunkingService(db_session)
        with pytest.raises(DocumentProcessingError):
            await svc.chunk_document(document.id)

    @pytest.mark.asyncio
    async def test_rechunking_is_idempotent(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_processed_document(
            db_session,
            project.id,
            user.id,
            "Repeated chunking test. " * 50,
        )

        svc = ChunkingService(db_session)
        first_chunks = await svc.chunk_document(document.id)
        second_chunks = await svc.chunk_document(document.id)

        repo = ChunkRepository(db_session)
        count = await repo.count_by_document(document.id)
        assert count == len(second_chunks)
        assert len(first_chunks) == len(second_chunks)


# ---------------------------------------------------------------------------
# Integration tests — ChunkRepository directly
# ---------------------------------------------------------------------------

class TestChunkRepository:
    @pytest.mark.asyncio
    async def test_create_bulk_and_get_by_document(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_processed_document(db_session, project.id, user.id)

        repo = ChunkRepository(db_session)
        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                chunk_text=f"chunk {i}",
                chunk_size=len(f"chunk {i}"),
                start_char=i * 10,
                end_char=(i + 1) * 10,
            )
            for i in range(3)
        ]
        created = await repo.create_bulk(chunks)
        assert len(created) == 3

        fetched = await repo.get_by_document(document.id)
        assert len(fetched) == 3
        assert [c.chunk_index for c in fetched] == [0, 1, 2]

    @pytest.mark.asyncio
    async def test_delete_by_document(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_processed_document(db_session, project.id, user.id)

        repo = ChunkRepository(db_session)
        chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=0,
            chunk_text="delete me",
            chunk_size=9,
            start_char=0,
            end_char=9,
        )
        await repo.create_bulk([chunk])

        deleted = await repo.delete_by_document(document.id)
        assert deleted == 1
        remaining = await repo.get_by_document(document.id)
        assert remaining == []

    @pytest.mark.asyncio
    async def test_count_by_document(self, db_session: AsyncSession):
        user = await _make_user(db_session)
        project = await _make_project(db_session, user.id)
        document = await _make_processed_document(db_session, project.id, user.id)

        repo = ChunkRepository(db_session)
        chunks = [
            DocumentChunk(
                document_id=document.id,
                chunk_index=i,
                chunk_text=f"chunk {i}",
                chunk_size=7,
                start_char=i * 10,
                end_char=i * 10 + 7,
            )
            for i in range(5)
        ]
        await repo.create_bulk(chunks)
        count = await repo.count_by_document(document.id)
        assert count == 5
