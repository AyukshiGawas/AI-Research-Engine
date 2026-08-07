"""Extractor layer for document text extraction."""

from app.services.extractors.base import BaseExtractor, ExtractionResult
from app.services.extractors.docx import DOCXExtractor
from app.services.extractors.factory import ExtractorFactory
from app.services.extractors.markdown import MarkdownExtractor
from app.services.extractors.pdf import PDFExtractor
from app.services.extractors.txt import TXTExtractor

__all__ = [
    "BaseExtractor",
    "ExtractionResult",
    "PDFExtractor",
    "DOCXExtractor",
    "TXTExtractor",
    "MarkdownExtractor",
    "ExtractorFactory",
]
