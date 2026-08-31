"""Domain-specific exceptions for the backend application."""

from __future__ import annotations


class AppException(Exception):
    """Base exception for application-level errors."""


class DocumentNotFoundError(AppException):
    """Raised when a document cannot be found in the current project context."""


class DuplicateDocumentError(AppException):
    """Raised when a duplicate document is detected in the same project."""


class InvalidDocumentTypeError(AppException):
    """Raised when a document filename or MIME type is invalid."""


class FileTooLargeError(AppException):
    """Raised when a document exceeds the configured size limit."""


class StorageFailureError(AppException):
    """Raised when the storage backend cannot persist or delete a file."""


class UnauthorizedDocumentAccessError(AppException):
    """Raised when the caller does not have access to the document project."""


class DocumentProcessingError(AppException):
    """Raised when an error occurs during document processing."""


class UnsupportedDocumentTypeError(AppException):
    """Raised when a document type is unsupported for text extraction."""


class DocumentExtractionError(AppException):
    """Raised when text extraction fails for a document."""


class ChunkingError(AppException):
    """Raised when document text chunking fails."""


class EmbeddingError(AppException):
    """Raised when embedding generation fails for a document chunk."""


class ChatError(AppException):
    """Raised when RAG chat generation fails."""

