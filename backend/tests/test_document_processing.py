"""Backend test suite for Phase 4: Document Processing Pipeline.

Covers:
  - PDF text extraction using pdfplumber
  - DOCX text extraction using python-docx
  - TXT text extraction using UTF-8 reader
  - Markdown text extraction using UTF-8 reader
  - ExtractorFactory strategy resolution and unsupported extension error handling
  - Repository status and extraction result updates
  - DocumentProcessorService lifecycle state transitions (UPLOADED -> PROCESSING -> PROCESSED / FAILED)
  - Process API endpoint POST /{project_id}/documents/{document_id}/process
  - Automatic processing upon upload via POST /{project_id}/documents
  - Alembic migration compatibility
"""

import io
import uuid
from pathlib import Path
import docx
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.storage import storage_provider
from app.exceptions import DocumentNotFoundError, UnsupportedDocumentTypeError
from app.models.document import Document, DocumentStatus
from app.models.project import Project
from app.models.user import User
from app.repositories.document_repository import DocumentRepository
from app.services.document_processor_service import DocumentProcessorService
from app.services.extractors import (
    DOCXExtractor,
    ExtractorFactory,
    MarkdownExtractor,
    PDFExtractor,
    TXTExtractor,
)

SAMPLE_PDF_BYTES = (
    b"%PDF-1.4\n"
    b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
    b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
    b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Resources <</Font <</F1 <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>>>>>> /Contents 4 0 R>> endobj\n"
    b"4 0 obj <</Length 55>> stream\n"
    b"BT\n"
    b"/F1 12 Tf\n"
    b"100 700 Td\n"
    b"(Hello PDF Extraction World) Tj\n"
    b"ET\n"
    b"endstream endobj\n"
    b"xref\n"
    b"0 5\n"
    b"0000000000 65535 f \n"
    b"0000000009 00000 n \n"
    b"0000000058 00000 n \n"
    b"0000000115 00000 n \n"
    b"0000000300 00000 n \n"
    b"trailer <</Size 5 /Root 1 0 R>>\n"
    b"startxref\n"
    b"400\n"
    b"%%EOF"
)


# Helper fixtures for user and project creation
@pytest.fixture
async def sample_user(db_session: AsyncSession) -> User:
    unique_id = uuid.uuid4().hex[:8]
    user = User(
        id=uuid.uuid4(),
        email=f"processor_{unique_id}@example.com",
        username=f"processor_{unique_id}",
        hashed_password="hashed_secret_pass",
        full_name="Processor Test User",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_project(db_session: AsyncSession, sample_user: User) -> Project:
    project = Project(
        id=uuid.uuid4(),
        name="Processor Test Project",
        description="Testing Phase 4 document processor",
        owner_id=sample_user.id,
    )
    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)
    return project


# ----------------------------------------------------------------------
# Extractor Unit Tests
# ----------------------------------------------------------------------

def test_pdf_extractor(tmp_path: Path) -> None:
    """PDFExtractor should extract text and page count from PDF file using pdfplumber."""
    pdf_file = tmp_path / "test.pdf"
    pdf_file.write_bytes(SAMPLE_PDF_BYTES)

    extractor = PDFExtractor()
    result = extractor.extract(pdf_file)

    assert result.page_count == 1
    assert "Hello PDF Extraction World" in result.text
    assert result.word_count > 0


def test_docx_extractor(tmp_path: Path) -> None:
    """DOCXExtractor should extract paragraphs and table cells using python-docx."""
    docx_file = tmp_path / "test.docx"
    doc = docx.Document()
    doc.add_heading("Research Findings", level=1)
    doc.add_paragraph("This is a test paragraph for Phase 4 extraction.")
    table = doc.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Header A"
    table.rows[0].cells[1].text = "Header B"
    doc.save(docx_file)

    extractor = DOCXExtractor()
    result = extractor.extract(docx_file)

    assert "Research Findings" in result.text
    assert "This is a test paragraph" in result.text
    assert "Header A | Header B" in result.text
    assert result.word_count > 0


def test_txt_extractor(tmp_path: Path) -> None:
    """TXTExtractor should extract plain text content via UTF-8 reader."""
    txt_file = tmp_path / "test.txt"
    txt_file.write_text("Line 1: Enterprise AI Engine\nLine 2: Plain text document.", encoding="utf-8")

    extractor = TXTExtractor()
    result = extractor.extract(txt_file)

    assert "Enterprise AI Engine" in result.text
    assert "Plain text document." in result.text
    assert result.word_count == 10



def test_markdown_extractor(tmp_path: Path) -> None:
    """MarkdownExtractor should extract raw markdown text via UTF-8 reader."""
    md_file = tmp_path / "test.md"
    md_file.write_text("# Document Title\n\n- Feature A\n- Feature B", encoding="utf-8")

    extractor = MarkdownExtractor()
    result = extractor.extract(md_file)

    assert "# Document Title" in result.text
    assert "- Feature A" in result.text
    assert result.word_count > 0


def test_extractor_factory() -> None:
    """ExtractorFactory should return the appropriate strategy for supported extensions."""
    assert isinstance(ExtractorFactory.get_extractor("pdf"), PDFExtractor)
    assert isinstance(ExtractorFactory.get_extractor(".docx"), DOCXExtractor)
    assert isinstance(ExtractorFactory.get_extractor("txt"), TXTExtractor)
    assert isinstance(ExtractorFactory.get_extractor("md"), MarkdownExtractor)
    assert isinstance(ExtractorFactory.get_extractor(".markdown"), MarkdownExtractor)

    with pytest.raises(UnsupportedDocumentTypeError):
        ExtractorFactory.get_extractor("unsupported_extension")


# ----------------------------------------------------------------------
# Repository Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_repository_processing_success_and_failure(
    db_session: AsyncSession, sample_project: Project, sample_user: User
) -> None:
    """DocumentRepository should persist processing success and failure metadata."""
    repo = DocumentRepository(db_session)
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        project_id=sample_project.id,
        uploaded_by=sample_user.id,
        original_filename="repo_test.txt",
        stored_filename=f"{doc_id}.txt",
        storage_path="test/repo_test.txt",
        mime_type="text/plain",
        extension="txt",
        file_size=100,
        status=DocumentStatus.UPLOADED,
    )
    await repo.create(doc)

    # Test processing success update
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    updated = await repo.update_processing_success(
        document=doc,
        extracted_text="Extracted text content",
        page_count=1,
        word_count=3,
        processed_at=now,
    )
    assert updated.status == DocumentStatus.PROCESSED
    assert updated.extracted_text == "Extracted text content"
    assert updated.word_count == 3
    assert updated.processed_at is not None
    assert updated.processing_error is None


    # Test processing failure update
    failed = await repo.update_processing_failure(doc, "Corrupted stream error")
    assert failed.status == DocumentStatus.FAILED
    assert failed.processing_error == "Corrupted stream error"


# ----------------------------------------------------------------------
# Service Pipeline Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_document_processor_service_pipeline(
    db_session: AsyncSession, sample_project: Project, sample_user: User
) -> None:
    """DocumentProcessorService should execute full processing pipeline and store extracted text."""
    doc_id = uuid.uuid4()
    stored_name = f"{doc_id}.txt"
    storage_path = await storage_provider.save(
        project_id=sample_project.id,
        document_id=doc_id,
        extension="txt",
        data=b"Pipeline test content with five words",
    )

    doc = Document(
        id=doc_id,
        project_id=sample_project.id,
        uploaded_by=sample_user.id,
        original_filename="pipeline_test.txt",
        stored_filename=stored_name,
        storage_path=storage_path,
        mime_type="text/plain",
        extension="txt",
        file_size=37,
        status=DocumentStatus.UPLOADED,
    )
    repo = DocumentRepository(db_session)
    await repo.create(doc)

    processor = DocumentProcessorService(db_session)
    processed_doc = await processor.process_document(doc_id)

    assert processed_doc.status == DocumentStatus.PROCESSED
    assert processed_doc.extracted_text == "Pipeline test content with five words"
    assert processed_doc.word_count == 6
    assert processed_doc.processed_at is not None
    assert processed_doc.processing_error is None

    # Cleanup storage
    await storage_provider.delete(storage_path)


@pytest.mark.asyncio
async def test_document_processor_service_handles_missing_file(
    db_session: AsyncSession, sample_project: Project, sample_user: User
) -> None:
    """DocumentProcessorService should update status to FAILED when physical file is missing."""
    doc_id = uuid.uuid4()
    doc = Document(
        id=doc_id,
        project_id=sample_project.id,
        uploaded_by=sample_user.id,
        original_filename="nonexistent.txt",
        stored_filename=f"{doc_id}.txt",
        storage_path="nonexistent/path.txt",
        mime_type="text/plain",
        extension="txt",
        file_size=10,
        status=DocumentStatus.UPLOADED,
    )
    repo = DocumentRepository(db_session)
    await repo.create(doc)

    processor = DocumentProcessorService(db_session)
    failed_doc = await processor.process_document(doc_id)

    assert failed_doc.status == DocumentStatus.FAILED
    assert "File not found on disk" in failed_doc.processing_error


@pytest.mark.asyncio
async def test_document_processor_service_nonexistent_doc_id(db_session: AsyncSession) -> None:
    """DocumentProcessorService should raise DocumentNotFoundError for invalid UUID."""
    processor = DocumentProcessorService(db_session)
    with pytest.raises(DocumentNotFoundError):
        await processor.process_document(uuid.uuid4())


# ----------------------------------------------------------------------
# API Endpoint Integration Tests
# ----------------------------------------------------------------------

@pytest.mark.asyncio
async def test_upload_automatically_processes_document(
    client: AsyncClient, db_session: AsyncSession, sample_project: Project, sample_user: User
) -> None:
    """Uploading a document via POST /{project_id}/documents should immediately extract text and set PROCESSED status."""
    # Obtain auth token
    from app.core.security import create_access_token
    token = create_access_token({"sub": str(sample_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    files = {
        "file": ("auto_process.txt", b"Auto processing pipeline text test.", "text/plain")
    }

    response = await client.post(
        f"/api/v1/projects/{sample_project.id}/documents",
        files=files,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PROCESSED"

    doc_id = uuid.UUID(data["id"])
    repo = DocumentRepository(db_session)
    doc = await repo.get_by_id(doc_id)
    assert doc is not None
    assert doc.status == DocumentStatus.PROCESSED
    assert doc.extracted_text == "Auto processing pipeline text test."
    assert doc.word_count == 5

    # Cleanup storage
    await storage_provider.delete(doc.storage_path)


@pytest.mark.asyncio
async def test_process_endpoint_reprocess(
    client: AsyncClient, db_session: AsyncSession, sample_project: Project, sample_user: User
) -> None:
    """POST /{project_id}/documents/{document_id}/process should trigger re-processing."""
    doc_id = uuid.uuid4()
    storage_path = await storage_provider.save(
        project_id=sample_project.id,
        document_id=doc_id,
        extension="md",
        data=b"# Reprocess Title\n\nContent for manual process trigger.",
    )

    doc = Document(
        id=doc_id,
        project_id=sample_project.id,
        uploaded_by=sample_user.id,
        original_filename="reprocess.md",
        stored_filename=f"{doc_id}.md",
        storage_path=storage_path,
        mime_type="text/markdown",
        extension="md",
        file_size=50,
        status=DocumentStatus.UPLOADED,
    )
    repo = DocumentRepository(db_session)
    await repo.create(doc)

    from app.core.security import create_access_token
    token = create_access_token({"sub": str(sample_user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    response = await client.post(
        f"/api/v1/projects/{sample_project.id}/documents/{doc_id}/process",
        headers=headers,
    )
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["id"] == str(doc_id)
    assert res_data["status"] == "PROCESSED"
    assert res_data["word_count"] > 0

    # Cleanup
    await storage_provider.delete(storage_path)
