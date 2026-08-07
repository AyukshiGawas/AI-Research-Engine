"""TXT text extractor implementation using UTF-8 reader."""

from pathlib import Path

from app.exceptions import DocumentExtractionError
from app.services.extractors.base import BaseExtractor, ExtractionResult


class TXTExtractor(BaseExtractor):
    """Text extractor for plain text (.txt) files."""

    def extract(self, file_path: Path) -> ExtractionResult:
        try:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    full_text = f.read().strip()
            except UnicodeDecodeError:
                with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                    full_text = f.read().strip()

            word_count = len(full_text.split()) if full_text else 0
            return ExtractionResult(
                text=full_text,
                page_count=None,
                word_count=word_count,
            )
        except Exception as exc:
            raise DocumentExtractionError(f"Failed to extract text from TXT file: {exc}") from exc
