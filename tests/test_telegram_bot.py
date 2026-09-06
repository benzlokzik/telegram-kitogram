"""Moderation and worker lifecycle checks without Telegram or model downloads."""

import asyncio
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from dialogue_kitogram.src.telegram_bot import SpamDetectionBot


class TelegramBotTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.model = MagicMock()
        with patch(
            "dialogue_kitogram.src.telegram_bot.load_spam_model",
            return_value=self.model,
        ):
            self.service = SpamDetectionBot("123456:local-test-token")
        self.service.bot = AsyncMock()
        self.service.db = AsyncMock()
        self.message = SimpleNamespace(
            message_id=42,
            chat=SimpleNamespace(id=-123),
            from_user=SimpleNamespace(id=7, username="test_user", is_bot=False),
            text="Купи сейчас!",
            caption=None,
        )

    async def asyncTearDown(self) -> None:
        await self.service.stop()

    async def test_spam_is_deleted_and_recorded(self) -> None:
        self.model.predict_proba.return_value = 0.99
        await self.service._check_and_handle_message(self.message)
        self.service.bot.delete_message.assert_awaited_once_with(-123, 42)
        kwargs = self.service.db.record_bot_message.call_args.kwargs
        self.assertEqual(kwargs["spam_probability"], 0.99)
        self.assertTrue(kwargs["was_deleted"])

    async def test_below_threshold_and_boundary_are_kept(self) -> None:
        for probability in (0.01, 0.95):
            with self.subTest(probability=probability):
                self.model.predict_proba.return_value = probability
                await self.service._check_and_handle_message(self.message)
        self.service.bot.delete_message.assert_not_awaited()
        self.service.db.record_bot_message.assert_not_awaited()

    async def test_existing_text_adjustments_are_preserved(self) -> None:
        self.model.predict_proba.return_value = 0.99
        for text in ("Купи\nсейчас!", "Здесь больше пяти слов в одном сообщении"):
            with self.subTest(text=text):
                self.message.text = text
                await self.service._check_and_handle_message(self.message)
        self.service.bot.delete_message.assert_not_awaited()

    async def test_commands_empty_text_and_bots_are_skipped(self) -> None:
        for text, is_bot in (("/start", False), ("  ", False), ("Купи!", True)):
            with self.subTest(text=text, is_bot=is_bot):
                self.message.text = text
                self.message.from_user.is_bot = is_bot
                await self.service._check_and_handle_message(self.message)
        self.model.predict_proba.assert_not_called()

    async def test_inference_failure_does_not_delete_message(self) -> None:
        self.model.predict_proba.side_effect = RuntimeError("inference failed")
        with patch("dialogue_kitogram.src.telegram_bot.logger.exception") as log_error:
            await self.service._check_and_handle_message(self.message)
        log_error.assert_called_once()
        self.service.bot.delete_message.assert_not_awaited()
        self.service.db.record_bot_message.assert_not_awaited()

    async def test_failed_deletion_is_recorded(self) -> None:
        self.model.predict_proba.return_value = 0.99
        self.service.bot.delete_message.side_effect = RuntimeError("missing permission")
        with patch("dialogue_kitogram.src.telegram_bot.logger.exception") as log_error:
            await self.service._check_and_handle_message(self.message)
        log_error.assert_called_once()
        self.assertFalse(
            self.service.db.record_bot_message.call_args.kwargs["was_deleted"],
        )

    async def test_inference_runs_outside_event_loop(self) -> None:
        loop_thread = threading.get_ident()
        self.model.predict_proba.side_effect = lambda _text: threading.get_ident()
        worker_thread = await self.service._predict_spam_probability("test")
        self.assertNotEqual(worker_thread, loop_thread)

    async def test_cancelled_inference_keeps_single_worker(self) -> None:
        loop = asyncio.get_running_loop()
        started = asyncio.Event()
        release = threading.Event()
        second_started = threading.Event()

        def predict(text: str) -> float:
            if text == "first":
                loop.call_soon_threadsafe(started.set)
                if not release.wait(timeout=5):
                    msg = "test did not release inference"
                    raise TimeoutError(msg)
            else:
                second_started.set()
            return 0.99

        self.model.predict_proba.side_effect = predict
        first = asyncio.create_task(self.service._predict_spam_probability("first"))
        second = None
        try:
            await asyncio.wait_for(started.wait(), timeout=5)
            first.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await first
            second = asyncio.create_task(
                self.service._predict_spam_probability("second"),
            )
            await asyncio.sleep(0.05)
            self.assertFalse(second_started.is_set())
        finally:
            release.set()
            await asyncio.gather(first, return_exceptions=True)
            if second is not None:
                self.assertEqual(await asyncio.wait_for(second, timeout=5), 0.99)

    async def test_manual_deletion_uses_async_model(self) -> None:
        handler = next(
            item.callback
            for item in self.service.dp.message.handlers
            if item.callback.__name__ == "delete_by_reply_command"
        )
        self.message.reply_to_message = SimpleNamespace(
            message_id=41,
            text="Реклама\nсо ссылкой",
            caption=None,
            from_user=self.message.from_user,
        )
        self.message.reply = AsyncMock()
        with (
            patch(
                "dialogue_kitogram.src.telegram_bot.get_admin_user_ids",
                return_value=[7],
            ),
            patch.object(
                self.service,
                "_predict_spam_probability",
                new_callable=AsyncMock,
                return_value=0.99,
            ) as predict,
        ):
            await handler(self.message)
        predict.assert_awaited_once_with("Реклама\nсо ссылкой")
        kwargs = self.service.db.record_bot_message.call_args.kwargs
        self.assertEqual(kwargs["spam_probability"], 0.99)
        self.assertTrue(kwargs["was_manual"])


if __name__ == "__main__":
    unittest.main()
