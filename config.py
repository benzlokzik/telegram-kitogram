"""Configuration module for loading environment variables."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file if it exists
_loaded = False

def load_config() -> None:
    """Load environment variables from .env file if it exists."""
    global _loaded
    if not _loaded:
        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)  # Use Path object instead of string
        _loaded = True


def get_telegram_token() -> str | None:
    """Get Telegram bot token from environment."""
    load_config()
    return os.getenv("TELEGRAM_BOT_TOKEN")


def get_spam_threshold() -> float:
    """Get spam detection threshold from environment."""
    load_config()
    try:
        return float(os.getenv("SPAM_THRESHOLD", "0.95"))
    except (ValueError, TypeError):
        return 0.95


def get_db_path() -> str:
    """Get database path from environment."""
    load_config()
    return os.getenv("DB_PATH", "bot_messages.db")


def get_log_level() -> str:
    """Get log level from environment."""
    load_config()
    return os.getenv("LOG_LEVEL", "INFO")


def get_log_file_path() -> str:
    """Get log file path from environment."""
    load_config()
    return os.getenv("LOG_FILE_PATH", "logs/bot.log")


# Load configuration when module is imported
load_config()