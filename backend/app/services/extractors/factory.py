"""Extractor factory for selecting the appropriate extractor strategy."""

from app.exceptions import UnsupportedDocumentTypeError
from app.services.extractors.base import BaseExtractor
from app.services.extractors.docx import DOCXExtractor
from app.services.extractors.markdown import MarkdownExtractor
from app.services.extractors.pdf import PDFExtractor
from app.services.extractors.txt import TXTExtractor


class ExtractorFactory:
    """Factory creating format-specific BaseExtractor instances based on file extension."""

    @staticmethod
    def get_extractor(extension: str) -> BaseExtractor:
        """Return the concrete BaseExtractor strategy for the given file extension.

        Args:
            extension: File extension (e.g., 'pdf', 'docx', 'txt', 'md').

        Returns:
            An instance of BaseExtractor subclass.

        Raises:
            UnsupportedDocumentTypeError: If no extractor exists for the extension.
        """
        ext = extension.lower().lstrip(".")
        if ext == "pdf":
            return PDFExtractor()
        elif ext == "docx":
            return DOCXExtractor()
        elif ext == "txt":
            return TXTExtractor()
        elif ext in ("md", "markdown"):
            return MarkdownExtractor()
        else:
            raise UnsupportedDocumentTypeError(f"Unsupported document format: '.{ext}'")
