"""Database foundation tests for the Document model."""

from app.models.document import Document, DocumentStatus


def test_document_model_exposes_requested_schema_fields() -> None:
    """The ORM model should expose the requested document columns and lifecycle enum."""
    columns = {column.name for column in Document.__table__.columns}

    expected_columns = {
        "id",
        "project_id",
        "uploaded_by",
        "original_filename",
        "stored_filename",
        "storage_path",
        "mime_type",
        "extension",
        "file_size",
        "status",
        "processed_at",
        "extracted_text",
        "processing_error",
        "page_count",
        "word_count",
        "created_at",
        "updated_at",
    }


    assert expected_columns <= columns
    assert DocumentStatus.UPLOADED.value == "UPLOADED"
    assert DocumentStatus.PROCESSING.value == "PROCESSING"
    assert DocumentStatus.PROCESSED.value == "PROCESSED"
    assert DocumentStatus.FAILED.value == "FAILED"
