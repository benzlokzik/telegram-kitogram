"""Offline checks for the released transformer model integration."""

import os
import unittest
from unittest.mock import patch

from dialogue_kitogram.src.config import get_spam_model_id, get_spam_model_revision
from dialogue_kitogram.src.spam_model import load_spam_model


class SpamModelTests(unittest.TestCase):
    def test_default_model_is_pinned(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            self.assertEqual(get_spam_model_id(), "benzlokzik/spam-detector-bert")
            self.assertEqual(
                get_spam_model_revision(),
                "3dd73bd4dcff411d44e1bc1a8e90d0568ca04395",
            )

    def test_loads_configured_snapshot_as_pretrained_model(self) -> None:
        with (
            patch.dict(
                os.environ,
                {"SPAM_MODEL_ID": "test/model", "SPAM_MODEL_REVISION": "test-revision"},
            ),
            patch("dialogue_kitogram.src.spam_model.setup_logging"),
            patch("dialogue_kitogram.src.spam_model.snapshot_download") as download,
            patch("dialogue_kitogram.src.spam_model.BertSpamModel") as model_class,
        ):
            download.return_value = "/cached/model"
            model = load_spam_model()

        self.assertIs(model, model_class.return_value)
        download.assert_called_once()
        self.assertEqual(download.call_args.kwargs["repo_id"], "test/model")
        self.assertEqual(download.call_args.kwargs["revision"], "test-revision")
        self.assertIn("*.safetensors", download.call_args.kwargs["allow_patterns"])
        self.assertEqual(model_class.call_args.args[1].pretrained, "/cached/model")
        model.load.assert_called_once_with()
        model.fit.assert_not_called()

    def test_download_failure_stops_startup(self) -> None:
        with (
            patch("dialogue_kitogram.src.spam_model.setup_logging"),
            patch(
                "dialogue_kitogram.src.spam_model.snapshot_download",
                side_effect=OSError("model unavailable"),
            ),
            patch("dialogue_kitogram.src.spam_model.BertSpamModel") as model_class,
            self.assertRaisesRegex(OSError, "model unavailable"),
        ):
            load_spam_model()
        model_class.assert_not_called()

    def test_invalid_weights_stop_startup(self) -> None:
        with (
            patch("dialogue_kitogram.src.spam_model.setup_logging"),
            patch("dialogue_kitogram.src.spam_model.snapshot_download"),
            patch("dialogue_kitogram.src.spam_model.BertSpamModel") as model_class,
        ):
            model_class.return_value.load.side_effect = ValueError("invalid weights")
            with self.assertRaisesRegex(ValueError, "invalid weights"):
                load_spam_model()


if __name__ == "__main__":
    unittest.main()
