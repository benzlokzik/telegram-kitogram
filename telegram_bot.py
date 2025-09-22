"""Telegram bot for detecting and deleting bot messages using spam detection."""

import asyncio

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command
from aiogram.enums import ChatType
from aiogram.types import Message
from loguru import logger
from bot_database import BotMessageDatabase
from config import get_spam_threshold, get_telegram_token, get_admin_user_ids
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

    def _setup_handlers(self) -> None:
        """Setup message and command handlers."""

        @self.dp.message(Command("start"))
        async def start_command(message: Message) -> None:
            """Handle /start command."""
            await message.reply(
                "Bot ready. I monitor messages and remove ones likely bot-generated."
            )

        @self.dp.message(Command("allow"))
        async def allow_command(message: Message) -> None:
            """Allow a chat for moderation. Only admins via DM can use.

            Usage in DM: /allow <chat_id> [title]
            When used in a group: /allow (adds current chat)
            """
            admin_ids = set(get_admin_user_ids())
            if message.chat.type == ChatType.PRIVATE:
                if message.from_user.id not in admin_ids:
                    await message.reply("Not authorized.")
                    return
                args = (message.text or "").split(maxsplit=2)
                if len(args) < 2:
                    await message.reply("Usage: /allow <chat_id> [title]")
                    return
                try:
                    target_chat_id = int(args[1])
                except ValueError:
                    await message.reply("chat_id must be an integer")
                    return
                title = args[2] if len(args) > 2 else None
                await self.db.add_allowed_chat(
                    chat_id=target_chat_id,
                    title=title,
                    added_by_admin_id=message.from_user.id,
                )
                await message.reply(f"Allowed chat {target_chat_id}.")
            else:
                # In a group/supergroup context, allow current chat
                if message.from_user.id not in admin_ids:
                    await message.reply("Not authorized.")
                    return
                await self.db.add_allowed_chat(
                    chat_id=message.chat.id,
                    title=getattr(message.chat, "title", None),
                    added_by_admin_id=message.from_user.id,
                )
                await message.reply("This chat is now allowed.")

        @self.dp.message(Command("disallow"))
        async def disallow_command(message: Message) -> None:
            """Remove a chat from allowed list. Admin DM or in group.

            Usage in DM: /disallow <chat_id>
            In group: /disallow (removes current chat)
            """
            admin_ids = set(get_admin_user_ids())
            if message.from_user.id not in admin_ids:
                await message.reply("Not authorized.")
                return
            if message.chat.type == ChatType.PRIVATE:
                args = (message.text or "").split(maxsplit=1)
                if len(args) < 2:
                    await message.reply("Usage: /disallow <chat_id>")
                    return
                try:
                    target_chat_id = int(args[1])
                except ValueError:
                    await message.reply("chat_id must be an integer")
                    return
            else:
                target_chat_id = message.chat.id
            removed = await self.db.remove_allowed_chat(target_chat_id)
            if removed:
                await message.reply(f"Disallowed chat {target_chat_id}.")
            else:
                await message.reply("Chat was not in allowed list.")

        @self.dp.message(Command("allowed"))
        async def allowed_command(message: Message) -> None:
            """List allowed chats. Only admins via DM."""
            admin_ids = set(get_admin_user_ids())
            if message.chat.type != ChatType.PRIVATE or message.from_user.id not in admin_ids:
                await message.reply("Not authorized.")
                return
            rows = await self.db.list_allowed_chats()
            if not rows:
                await message.reply("No allowed chats.")
                return
            lines = [
                f"{row['chat_id']} — {row.get('title') or ''} (by {row.get('added_by_admin_id')})"
                for row in rows
            ]
            await message.reply("Allowed chats:\n" + "\n".join(lines))

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
            # Enforce allowed chats for group/supergroup channels; allow DMs for admins
            if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
                if not await self.db.is_chat_allowed(message.chat.id):
                    return
            elif message.chat.type == ChatType.PRIVATE:
                # Only respond to admins in DM; others get a short notice
                if message.from_user.id not in set(get_admin_user_ids()):
                    await message.reply("Hi! Ask an admin to add your group via /allow.")
                    return
            await self._check_and_handle_message(message)

        @self.dp.message()
        async def process_other_messages(message: Message) -> None:
            """Process non-text messages (images, stickers, etc.)."""
            # For non-text messages, we can't analyze the content but we log a trace
            logger.debug("Received non-text message in chat {} of type {}",
                         message.chat.id, message.chat.type)

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

            logger.info(
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
                    logger.info(
                        f"Deleted bot message from {message.from_user.username} "
                        f"with probability {spam_probability:.3f}",
                    )
                except Exception as e:
                    logger.exception("Failed to delete message: {}", e)

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
            logger.exception("Error processing message: {}", e)

    async def start(self) -> None:
        """Start the bot."""
        await self.db.init_database()
        logger.info("Bot database initialized")

        logger.info("Starting bot...")
        await self.dp.start_polling(self.bot)

    async def stop(self) -> None:
        """Stop the bot."""
        logger.info("Stopping bot...")
        await self.bot.session.close()


async def main() -> None:
    """Main function to run the bot."""
    # Get bot token from environment variable
    token = get_telegram_token()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment")
        logger.error("Please copy .env.example to .env and set your bot token")
        return

    # Create and start bot
    spam_threshold = get_spam_threshold()
    bot = SpamDetectionBot(token, spam_threshold=spam_threshold)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
