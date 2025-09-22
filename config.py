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


def get_admin_user_ids() -> list[int]:
    """Get list of Telegram admin user IDs from env `ADMIN_USER_IDS`.

    Supports comma/space separated integers, e.g. "123,456" or "123 456".
    Returns an empty list if unset or invalid.
    """
    load_config()
    raw = os.getenv("ADMIN_USER_IDS", "").strip()
    if not raw:
        # Backward/alias support
        raw = os.getenv("ADMIN_IDS", "").strip()
    if not raw:
        return []
    # Normalize separators to commas, split, and parse ints safely
    separators_normalized = raw.replace(" ", ",")
    ids: list[int] = []
    for token in separators_normalized.split(","):
        token = token.strip()
        if not token:
            continue
        try:
            ids.append(int(token))
        except ValueError:
            # ignore invalid tokens
            continue
    # De-duplicate while preserving order
    seen: set[int] = set()
    unique_ids: list[int] = []
    for admin_id in ids:
        if admin_id not in seen:
            unique_ids.append(admin_id)
            seen.add(admin_id)
    return unique_ids
