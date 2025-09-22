"""Logging configuration using loguru."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger

# Load environment variables first
env_file = Path(".env")
if env_file.exists():
    load_dotenv(env_file)

log_format = (
    " | "
    "<level>{level: <8}</level> | "
    "<cyan>{file}</cyan>:<cyan>{line}</cyan>:(<cyan>{function}</cyan>) "
    "- <level>{message}</level>"
)


def setup_logging() -> None:
    """Configure loguru logging with the provided cool config."""
    log_file_path = os.getenv("LOG_FILE_PATH", "logs/bot.log")
    log_level = os.getenv("LOG_LEVEL", "INFO")

    # Create logs directory if it doesn't exist
    Path(log_file_path).parent.mkdir(exist_ok=True)

    # Configure Loguru
    logger.remove()
    logger.add(sys.stdout, format=log_format, level="DEBUG")
    logger.add(
        log_file_path,
        format=log_format,
        level=log_level,
        encoding="utf-8",
        mode="a",
    )


# Setup logging when module is imported
setup_logging()
