"""Abstract storage provider interface and LocalStorageProvider implementation.

Abstracting disk I/O behind a StorageProvider interface allows Phase 4+ to swap
LocalStorageProvider for an S3StorageProvider without touching service logic.

Usage:
    from app.core.storage import storage_provider
    path = await storage_provider.save(project_id, document_id, extension, content_bytes)
"""

import hashlib
import shutil
import uuid
from abc import ABC, abstractmethod
from pathlib import Path

from app.core.logging import logger


class StorageProvider(ABC):
    """Abstract interface for document binary storage operations."""

    @abstractmethod
    async def save(
        self,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
        extension: str,
        data: bytes,
    ) -> str:
        """Persist document bytes and return the relative storage path."""

    @abstractmethod
    async def delete(self, storage_path: str) -> None:
        """Remove a previously stored file by its relative storage path."""

    @abstractmethod
    def resolve(self, storage_path: str) -> Path:
        """Return the absolute filesystem path for a stored file."""


class LocalStorageProvider(StorageProvider):
    """Stores documents on the local filesystem under UPLOAD_DIR.

    File layout:  {upload_dir}/{project_id}/{document_id}.{extension}
    """

    def __init__(self, upload_dir: Path) -> None:
        self._upload_dir = upload_dir
        self._upload_dir.mkdir(parents=True, exist_ok=True)

    async def save(
        self,
        project_id: uuid.UUID,
        document_id: uuid.UUID,
        extension: str,
        data: bytes,
    ) -> str:
        """Write bytes to disk and return the relative path.

        Args:
            project_id: UUID of the owning project workspace.
            document_id: UUID assigned to this document record.
            extension: Clean file extension WITHOUT dot, e.g. ``"pdf"``.
            data: Raw file bytes.

        Returns:
            Relative storage path string, e.g. ``"uploads/abc.../def....pdf"``.
        """
        project_dir = self._upload_dir / str(project_id)
        project_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{document_id}.{extension}"
        abs_path = project_dir / filename
        abs_path.write_bytes(data)

        relative_path = f"uploads/{project_id}/{filename}"
        logger.debug(f"STORAGE | saved | path={relative_path} | size={len(data)}")
        return relative_path

    async def delete(self, storage_path: str) -> None:
        """Remove file at the given relative storage path.

        Args:
            storage_path: Relative path returned by :meth:`save`.
        """
        abs_path = self.resolve(storage_path)
        if abs_path.exists():
            abs_path.unlink()
            logger.debug(f"STORAGE | deleted | path={storage_path}")
        else:
            logger.warning(f"STORAGE | delete miss | path={storage_path}")

    def resolve(self, storage_path: str) -> Path:
        """Construct absolute path from a relative storage path.

        Args:
            storage_path: e.g. ``"uploads/{project_id}/{document_id}.pdf"``

        Returns:
            Absolute ``Path`` object on the local filesystem.
        """
        # Strip leading "uploads/" prefix; files live under self._upload_dir
        relative = storage_path.removeprefix("uploads/")
        return self._upload_dir / relative


def compute_sha256(data: bytes) -> str:
    """Compute SHA-256 hex digest for duplicate detection and integrity checks."""
    return hashlib.sha256(data).hexdigest()


# ---------------------------------------------------------------------------
# Module-level singleton — import this everywhere instead of instantiating.
# ---------------------------------------------------------------------------
from app.core.config import settings  # noqa: E402 (avoid circular at top-level)

_upload_dir = Path(settings.UPLOAD_DIR)
storage_provider: StorageProvider = LocalStorageProvider(upload_dir=_upload_dir)
