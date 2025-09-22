"""Stub entrypoint that delegates to dialogue_kitogram.src.main."""

import asyncio

from dialogue_kitogram.src.telegram_bot import main

if __name__ == "__main__":
    asyncio.run(main())
