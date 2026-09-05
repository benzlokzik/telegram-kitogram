"""Exercise real aiogram polling backpressure without Telegram network calls."""

import asyncio
import unittest
from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

from aiogram import Bot, Dispatcher
from aiogram.types import Chat, Message, Update, User
from dialogue_kitogram.src.telegram_bot import (
    MAX_CONCURRENT_UPDATES,
    SpamDetectionBot,
)


async def _finish_polling(
    service: SpamDetectionBot,
    polling: asyncio.Task[None],
    drained: asyncio.Event,
) -> None:
    try:
        await asyncio.wait_for(drained.wait(), timeout=5)
        await asyncio.wait_for(service.dp.stop_polling(), timeout=5)
        await asyncio.wait_for(polling, timeout=5)
    finally:
        polling.cancel()
        await asyncio.gather(polling, return_exceptions=True)
        pending = list(service.dp._handle_update_tasks)
        for task in pending:
            task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        await service.stop()


class PollingTests(unittest.IsolatedAsyncioTestCase):
    async def test_polling_bounds_handlers_and_drains_after_release(self) -> None:
        limit = MAX_CONCURRENT_UPDATES
        total = limit * 2 + 1
        active = peak = completed = 0
        saturated = asyncio.Event()
        overflow = asyncio.Event()
        release = asyncio.Event()
        drained = asyncio.Event()
        keep_listening = asyncio.Event()
        user = User(id=7, is_bot=False, first_name="Test")

        async def handle_message(_message: Message) -> None:
            nonlocal active, peak, completed
            active += 1
            peak = max(peak, active)
            if active == limit:
                saturated.set()
            if active > limit:
                overflow.set()
            try:
                await release.wait()
            finally:
                active -= 1
                completed += 1
                if completed == total:
                    drained.set()

        async def updates(_bot: Bot, **_kwargs: object) -> AsyncIterator[Update]:
            for update_id in range(total):
                yield Update(
                    update_id=update_id,
                    message=Message(
                        message_id=update_id + 1,
                        date=datetime.now(UTC),
                        chat=Chat(id=-123, type="group"),
                        from_user=user,
                        text="Проверка ограничения обработки",
                    ),
                )
            await keep_listening.wait()

        with patch("dialogue_kitogram.src.telegram_bot.load_spam_model"):
            service = SpamDetectionBot("123456:local-test-token")
        service.db = AsyncMock()
        service.dp = Dispatcher()
        service.dp.message.register(handle_message)
        bot_user = User(id=123456, is_bot=True, first_name="Test Bot")
        with (
            patch.object(service.bot, "me", new=AsyncMock(return_value=bot_user)),
            patch.object(service.dp, "_listen_updates", new=updates),
        ):
            polling = asyncio.create_task(service.start())
            try:
                await asyncio.wait_for(saturated.wait(), timeout=5)
                with self.assertRaises(TimeoutError):
                    await asyncio.wait_for(overflow.wait(), timeout=0.05)
                self.assertEqual(active, limit)
                self.assertEqual(peak, limit)
            finally:
                release.set()
                await _finish_polling(service, polling, drained)
        self.assertEqual(completed, total)
        self.assertEqual(active, 0)
        self.assertFalse(service.dp._handle_update_tasks)


if __name__ == "__main__":
    unittest.main()
