"""Test script for the spam detection functionality."""

import asyncio
import math
import tempfile
from pathlib import Path

from loguru import logger

from dialogue_kitogram.src import log_config  # noqa: F401
from dialogue_kitogram.src.bot_database import BotMessageDatabase
from dialogue_kitogram.src.spam_model import load_spam_model

# Constants
SPAM_THRESHOLD = 0.95
TEST_SPAM_PROBABILITY = 0.97


async def test_spam_detection() -> bool:
    """Test the spam detection model."""
    logger.info("Testing spam detection model...")

    model = load_spam_model()
    logger.success("Model loaded successfully")

    # Test with various messages
    test_messages = [
        ("Hello everyone!", "normal message"),
        ("Срочно работа в Москве! З/п 150 000 руб! Писать в лс", "spam message"),
        ("блять как же заебали кустовые эйдоры сука ненавижу их всех", "toxic message"),
        ("qq", "short message"),
        ("Привет! Как дела?", "greeting"),
        ("ЗАРАБОТАЙ 1000000 РУБЛЕЙ ЗА ДЕНЬ!!! ПЕРЕХОДИ ПО ССЫЛКЕ!!!", "obvious spam"),
    ]

    logger.info("Testing different message types:")
    for message, description in test_messages:
        probability = model.predict_proba(message)
        if not math.isfinite(probability) or not 0.0 <= probability <= 1.0:
            logger.error("Invalid spam probability: {}", probability)
            return False
        status = (
            "Above raw threshold" if probability > SPAM_THRESHOLD else "Below threshold"
        )
        logger.info(f"{status} {description}: {probability:.3f} - '{message[:50]}...'")

    return True


async def test_database() -> bool:
    """Test the database functionality."""
    logger.info("Testing database functionality...")

    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    try:
        db = BotMessageDatabase(test_db_path)
        await db.init_database()
        logger.success("Database initialized successfully")

        # Test recording a message
        await db.record_bot_message(
            message_id=12345,
            chat_id=-67890,
            user_id=123,
            username="test_user",
            text_content="Test spam message",
            spam_probability=TEST_SPAM_PROBABILITY,
            was_deleted=True,
        )
        logger.success("Message recorded successfully")

        # Test getting stats
        stats = await db.get_stats()
        logger.success(f"Stats retrieved: {stats}")

        # Test getting recent detections
        recent = await db.get_recent_detections(limit=5)
        logger.success(f"Recent detections: {len(recent)} found")

        return True

    finally:
        # Clean up test database
        Path(test_db_path).unlink(missing_ok=True)


async def main() -> int:
    """Run all tests."""
    logger.info("🧪 Running tests for Telegram Admin Bot")

    success = True

    try:
        if not await test_spam_detection():
            success = False
    except Exception as e:
        logger.error(f"Spam detection test failed: {e}")
        success = False

    try:
        if not await test_database():
            success = False
    except Exception as e:
        logger.error(f"Database test failed: {e}")
        success = False

    if success:
        logger.success("All tests passed!")
        logger.info("To run the bot:")
        logger.info("1. Get a bot token from @BotFather on Telegram")
        logger.info("2. Copy .env.example to .env and set your bot token")
        logger.info("3. Run: uv run --locked --no-dev python main.py")
    else:
        logger.error("Some tests failed!")
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
