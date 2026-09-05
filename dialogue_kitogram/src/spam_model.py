"""Load the released spam-detector transformer with pinned, cached weights."""

from huggingface_hub import snapshot_download
from loguru import logger
from spam_detector.core.base_model import ModelConfig
from spam_detector.transformers.bert_model import BertSpamModel, BertTrainingConfig

from dialogue_kitogram.src.config import get_spam_model_id, get_spam_model_revision
from dialogue_kitogram.src.log_config import setup_logging


def load_spam_model() -> BertSpamModel:
    """Download a model snapshot and fail startup if it cannot be loaded."""
    # spam-detector configures global Loguru sinks during import.
    setup_logging()
    model_id = get_spam_model_id()
    revision = get_spam_model_revision()
    logger.info("Loading BERT spam model {} at revision {}", model_id, revision)
    model_path = snapshot_download(
        repo_id=model_id,
        revision=revision,
        allow_patterns=["*.json", "*.txt", "*.safetensors"],
    )
    model = BertSpamModel(
        ModelConfig(),
        BertTrainingConfig(pretrained=model_path),
    )
    model.load()
    logger.info("BERT spam model loaded")
    return model
