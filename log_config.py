"""Logging configuration using loguru."""

import sys
from pathlib import Path

from loguru import logger

log_format = (
    " | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}</cyan>:<cyan>{line}</cyan>:(<cyan>{function}</cyan>) "
    "- <level>{message}</level>"
)

log_file_path = "logs/bot.log"

def setup_logging() -> None:
    """Configure loguru logging with the provided cool config."""
    # Create logs directory if it doesn't exist
    Path(log_file_path).parent.mkdir(exist_ok=True)

    # Configure Loguru
    logger.remove()
    logger.add(sys.stdout, format=log_format, level="DEBUG")
    logger.add(
        log_file_path,
        format=log_format,
        level="INFO",
        encoding="utf-8",
        mode="a",
    )

# Setup logging when module is imported
setup_logging()
