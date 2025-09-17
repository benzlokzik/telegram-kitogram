"""Main entry point for the Telegram Admin Bot."""

import asyncio
import os
import sys

from loguru import logger

import log_config  # noqa: F401
from telegram_bot import SpamDetectionBot


def main() -> None:
    """Main function with options for running different components."""
    if len(sys.argv) > 1 and sys.argv[1] == "bot":
        # Run the Telegram bot
        asyncio.run(run_bot())
    else:
        logger.info("Telegram Admin Bot")
        logger.info("Usage:")
        logger.info("  python main.py bot    - Run the Telegram bot")
        logger.info("")
        logger.info("Before running the bot, set your TELEGRAM_BOT_TOKEN "
              "environment variable:")
        logger.info("  export TELEGRAM_BOT_TOKEN=your_bot_token_here")


async def run_bot() -> None:
    """Run the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set")
        logger.error("Please set it with your bot token from @BotFather")
        return

    bot = SpamDetectionBot(token, spam_threshold=0.95)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.stop()


if __name__ == "__main__":
    main()
