"""Main entry point for the Telegram Admin Bot."""

import asyncio
import os
import sys

from telegram_bot import SpamDetectionBot


def main() -> None:
    """Main function with options for running different components."""
    if len(sys.argv) > 1 and sys.argv[1] == "bot":
        # Run the Telegram bot
        asyncio.run(run_bot())
    else:
        print("Telegram Admin Bot")
        print("Usage:")
        print("  python main.py bot    - Run the Telegram bot")
        print()
        print("Before running the bot, set your TELEGRAM_BOT_TOKEN "
              "environment variable:")
        print("  export TELEGRAM_BOT_TOKEN=your_bot_token_here")


async def run_bot() -> None:
    """Run the Telegram bot."""
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set")
        print("Please set it with your bot token from @BotFather")
        return

    bot = SpamDetectionBot(token, spam_threshold=0.95)

    try:
        await bot.start()
    except KeyboardInterrupt:
        print("\nBot stopped by user")
    finally:
        await bot.stop()


if __name__ == "__main__":
    main()
