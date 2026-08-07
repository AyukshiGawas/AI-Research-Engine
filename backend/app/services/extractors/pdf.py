"""PDF text extractor implementation using pdfplumber."""

from pathlib import Path
import pdfplumber

from app.exceptions import DocumentExtractionError
from app.services.extractors.base import BaseExtractor, ExtractionResult


class PDFExtractor(BaseExtractor):
    """Text extractor for Portable Document Format (.pdf) files using pdfplumber."""

    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            pages_text = []
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    if text.strip():
                        pages_text.append(text.strip())

            full_text = "\n\n".join(pages_text).strip()
            word_count = len(full_text.split()) if full_text else 0
            return ExtractionResult(
                text=full_text,
                page_count=page_count,
                word_count=word_count,
            )
        except Exception as exc:
            raise DocumentExtractionError(f"Failed to extract text from PDF file: {exc}") from exc
