"""Main entry point for the Telegram Admin Bot."""

import asyncio

from loguru import logger

from config import get_spam_threshold, get_telegram_token
from telegram_bot import SpamDetectionBot


def main() -> None:
    """Main function with options for running different components."""
    # if len(sys.argv) == 1 or sys.argv[1] == "bot":
    #    # Run the Telegram bot by default (or when explicitly requested)
    asyncio.run(run_bot())
    # else:
    #     logger.info("Telegram Admin Bot")
    #     logger.info("Usage:")
    #     logger.info("  python main.py         - Run the Telegram bot (default)")
    #     logger.info("")
    #     logger.info("Configuration:")
    #     logger.info("  Copy .env.example to .env and configure your settings")
    #     logger.info("  Or set environment variables directly:")
    #     logger.info("  export TELEGRAM_BOT_TOKEN=your_bot_token_here")


async def run_bot() -> None:
    """Run the Telegram bot."""
    token = get_telegram_token()
    if not token:
        logger.error("TELEGRAM_BOT_TOKEN not found in environment")
        logger.error("Please copy .env.example to .env and set your bot token")
        logger.error("Or set TELEGRAM_BOT_TOKEN environment variable")
        return

    spam_threshold = get_spam_threshold()
    logger.info(f"Using spam threshold: {spam_threshold}")

    bot = SpamDetectionBot(token, spam_threshold=spam_threshold)

    try:
        await bot.start()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    finally:
        await bot.stop()


if __name__ == "__main__":
    main()
