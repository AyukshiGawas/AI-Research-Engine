"""Base class and result data structure for document text extractors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class ExtractionResult:
    """Encapsulates the plain text and statistics extracted from a document."""

    text: str
    page_count: Optional[int] = None
    word_count: Optional[int] = None


class BaseExtractor(ABC):
    """Abstract base class for format-specific text extractors."""

    @abstractmethod
    def extract(self, file_path: Path) -> ExtractionResult:
        """Extract plain text and metadata from the file at file_path.

        Args:
            file_path: Absolute path to the source document on disk.

        Returns:
            ExtractionResult instance containing plain text, page count, and word count.
        """
        pass
