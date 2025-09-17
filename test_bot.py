"""Test script for the spam detection functionality."""

import asyncio
import tempfile
from pathlib import Path

from bot_database import BotMessageDatabase
from dialogue_kitogram.src.fastspam.ft_model import FastTextSpamModel, ModelConfig

# Constants
SPAM_THRESHOLD = 0.95
TEST_SPAM_PROBABILITY = 0.97


async def test_spam_detection() -> bool:
    """Test the spam detection model."""
    print("Testing spam detection model...")

    # Initialize model
    cfg = ModelConfig()
    model = FastTextSpamModel(cfg)

    if not cfg.model_path.exists():
        print(f"Error: Model file not found at {cfg.model_path}")
        return False

    model.load()
    print("✅ Model loaded successfully")

    # Test with various messages
    test_messages = [
        ("Hello everyone!", "normal message"),
        ("Срочно работа в Москве! З/п 150 000 руб! Писать в лс", "spam message"),
        ("блять как же заебали кустовые эйдоры сука ненавижу их всех", "toxic message"),
        ("qq", "short message"),
        ("Привет! Как дела?", "greeting"),
        ("ЗАРАБОТАЙ 1000000 РУБЛЕЙ ЗА ДЕНЬ!!! ПЕРЕХОДИ ПО ССЫЛКЕ!!!", "obvious spam"),
    ]

    print("\nTesting different message types:")
    for message, description in test_messages:
        probability = model.predict_proba(message)
        status = ("🔴 BOT (would delete)" if probability > SPAM_THRESHOLD
                  else "🟢 HUMAN")
        print(f"{status} {description}: {probability:.3f} - "
              f"'{message[:50]}...'")

    return True


async def test_database() -> bool:
    """Test the database functionality."""
    print("\nTesting database functionality...")

    # Use temporary database for testing
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tmp:
        test_db_path = tmp.name

    try:
        db = BotMessageDatabase(test_db_path)
        await db.init_database()
        print("✅ Database initialized successfully")

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
        print("✅ Message recorded successfully")

        # Test getting stats
        stats = await db.get_stats()
        print(f"✅ Stats retrieved: {stats}")

        # Test getting recent detections
        recent = await db.get_recent_detections(limit=5)
        print(f"✅ Recent detections: {len(recent)} found")

        return True

    finally:
        # Clean up test database
        Path(test_db_path).unlink(missing_ok=True)


async def main() -> None:
    """Run all tests."""
    print("🧪 Running tests for Telegram Admin Bot\n")

    success = True

    try:
        if not await test_spam_detection():
            success = False
    except Exception as e:
        print(f"❌ Spam detection test failed: {e}")
        success = False

    try:
        if not await test_database():
            success = False
    except Exception as e:
        print(f"❌ Database test failed: {e}")
        success = False

    if success:
        print("\n✅ All tests passed!")
        print("\nTo run the bot:")
        print("1. Get a bot token from @BotFather on Telegram")
        print("2. Set environment variable: export TELEGRAM_BOT_TOKEN=your_token")
        print("3. Run: python main.py bot")
    else:
        print("\n❌ Some tests failed!")


if __name__ == "__main__":
    asyncio.run(main())
