"""Validation helpers for document upload requests."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from fastapi import UploadFile

from app.core.config import settings

_ALLOWED_EXTENSIONS: Final[set[str]] = set(settings.ALLOWED_EXTENSIONS)
_ALLOWED_MIME_TYPES: Final[dict[str, str]] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "txt": "text/plain",
    "md": "text/markdown",
}


class DocumentValidationError(ValueError):
    """Raised when a document upload fails validation."""


def validate_filename(filename: str | None) -> str:
    """Validate the user-supplied filename for path traversal and malformed input."""
    if not filename:
        raise DocumentValidationError("Filename is required.")

    name = Path(filename).name
    if not name or name in {".", ".."}:
        raise DocumentValidationError("Invalid filename.")

    if "/" in filename or "\\" in filename:
        raise DocumentValidationError("Invalid filename path.")

    if name.count(".") > 1:
        raise DocumentValidationError("Double extensions are not allowed.")

    return name


def validate_extension(filename: str) -> str:
    """Extract and validate the file extension."""
    original_name = validate_filename(filename)
    suffix = Path(original_name).suffix.lstrip(".").lower()
    if not suffix or suffix not in _ALLOWED_EXTENSIONS:
        raise DocumentValidationError(
            f"Unsupported file type '.{suffix}'. Allowed: {', '.join(sorted(_ALLOWED_EXTENSIONS))}."
        )
    return suffix


def validate_mime_type(extension: str, mime_type: str | None) -> str:
    """Validate the MIME type against the allowed extension mapping."""
    expected = _ALLOWED_MIME_TYPES.get(extension)
    if expected is None:
        raise DocumentValidationError(f"Unsupported extension: {extension}")
    if not mime_type:
        raise DocumentValidationError("MIME type is required.")
    if mime_type != expected:
        raise DocumentValidationError("MIME type does not match the declared file type.")
    return mime_type


async def read_upload_bytes(upload: UploadFile, max_bytes: int) -> bytes:
    """Read the upload stream into memory while enforcing the size limit."""
    chunks: list[bytes] = []
    total = 0

    while True:
        chunk = await upload.read(1024 * 64)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise DocumentValidationError(
                f"File exceeds the maximum allowed size of {max_bytes // (1024 * 1024)} MB."
            )
        chunks.append(chunk)

    if not chunks:
        raise DocumentValidationError("Empty files are not allowed.")

    return b"".join(chunks)
