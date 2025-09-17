"""Telegram bot for detecting and deleting bot messages using spam detection."""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.types import Message

from bot_database import BotMessageDatabase
from dialogue_kitogram.src.fastspam.ft_model import FastTextSpamModel, ModelConfig


class SpamDetectionBot:
    """Telegram bot that detects and removes spam/bot messages."""

    def __init__(self, token: str, spam_threshold: float = 0.95) -> None:
        self.bot = Bot(token=token)
        self.dp = Dispatcher()
        self.spam_threshold = spam_threshold
        self.db = BotMessageDatabase()

        # Initialize spam detection model
        cfg = ModelConfig()
        self.spam_model = FastTextSpamModel(cfg)
        self.spam_model.load()

        # Setup handlers
        self._setup_handlers()

        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.logger = logging.getLogger(__name__)

    def _setup_handlers(self) -> None:
        """Setup message and command handlers."""

        @self.dp.message(Command("start"))
        async def start_command(message: Message) -> None:
            """Handle /start command."""
            await message.reply(
                "Bot started! I will monitor messages and remove those that "
                "are likely bot-generated (>95% probability).",
            )

        @self.dp.message(Command("stats"))
        async def stats_command(message: Message) -> None:
            """Handle /stats command to show detection statistics."""
            stats = await self.db.get_stats()
            response = (
                f"📊 Detection Statistics:\n"
                f"Total detections: {stats['total_detections']}\n"
                f"Messages deleted: {stats['deleted_messages']}\n"
                f"Average spam probability: {stats['avg_spam_probability']:.2%}\n"
                f"Max spam probability: {stats['max_spam_probability']:.2%}"
            )
            await message.reply(response)

        @self.dp.message(Command("recent"))
        async def recent_command(message: Message) -> None:
            """Handle /recent command to show recent detections."""
            recent = await self.db.get_recent_detections(limit=5)
            if not recent:
                await message.reply("No recent detections found.")
                return

            response = "🔍 Recent detections:\n\n"
            for detection in recent:
                response += (
                    f"User: {detection['username'] or 'Unknown'}\n"
                    f"Probability: {detection['spam_probability']:.2%}\n"
                    f"Text: {detection['text_content'][:50]}...\n"
                    f"Deleted: {'✅' if detection['was_deleted'] else '❌'}\n"
                    f"Time: {detection['detection_timestamp']}\n\n"
                )
            await message.reply(response)

        @self.dp.message(F.text)
        async def process_text_message(message: Message) -> None:
            """Process incoming text messages for spam detection."""
            await self._check_and_handle_message(message)

        @self.dp.message()
        async def process_other_messages(message: Message) -> None:
            """Process non-text messages (images, stickers, etc.)."""
            # For non-text messages, we can't analyze the content
            # but we can still log them if needed

    async def _check_and_handle_message(self, message: Message) -> None:
        """Check message for spam and handle accordingly."""
        try:
            # Skip messages from bot itself and commands
            if (message.from_user.is_bot or
                (message.text and message.text.startswith("/"))):
                return

            text_content = message.text or message.caption or ""
            if not text_content.strip():
                return

            # Get spam probability
            spam_probability = self.spam_model.predict_proba(text_content)

            self.logger.info(
                f"Message from {message.from_user.username}: "
                f"spam_probability={spam_probability:.3f}, "
                f"threshold={self.spam_threshold}",
            )

            # If probability is above threshold, delete message and record it
            if spam_probability > self.spam_threshold:
                was_deleted = False
                try:
                    await self.bot.delete_message(message.chat.id, message.message_id)
                    was_deleted = True
                    self.logger.info(
                        f"Deleted bot message from {message.from_user.username} "
                        f"with probability {spam_probability:.3f}",
                    )
                except Exception as e:
                    self.logger.exception("Failed to delete message: %s", e)

                # Record in database
                await self.db.record_bot_message(
                    message_id=message.message_id,
                    chat_id=message.chat.id,
                    user_id=message.from_user.id,
                    username=message.from_user.username,
                    text_content=text_content,
                    spam_probability=spam_probability,
                    was_deleted=was_deleted,
                )

        except Exception as e:
            self.logger.exception("Error processing message: %s", e)

    async def start(self) -> None:
        """Start the bot."""
        await self.db.init_database()
        self.logger.info("Bot database initialized")

        self.logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        """Stop the bot."""
        self.logger.info("Stopping bot...")
        await self.bot.session.close()


async def main() -> None:
    """Main function to run the bot."""
    # Get bot token from environment variable
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Please set TELEGRAM_BOT_TOKEN environment variable")
        return

    # Create and start bot
    bot = SpamDetectionBot(token, spam_threshold=0.95)

    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
