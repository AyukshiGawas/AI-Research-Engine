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
