"""Logging configuration module for structured application logging."""

import logging
import sys
from app.core.config import settings


def configure_logging() -> None:
    """Configure structured logging for the backend application."""
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )


logger = logging.getLogger("app")
