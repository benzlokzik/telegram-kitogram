import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for spam detection model paths."""

    project_root: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
    data_subdir: str = "dialogue_kitogram/data"
    model_name: str = "antispam.ftz"
    train_name: str = "train_data.txt"

    @property
    def data_dir(self) -> pathlib.Path:
        return self.project_root / self.data_subdir

    @property
    def model_path(self) -> pathlib.Path:
        return self.data_dir / self.model_name

    @property
    def train_path(self) -> pathlib.Path:
        return (self.data_dir / self.train_name).absolute()


class SpamModel(ABC):
    """Abstract base class for spam detection models."""

    def __init__(self, cfg: ModelConfig) -> None:
        self.cfg = cfg

    @abstractmethod
    def fit(self) -> None: ...
    @abstractmethod
    def load(self) -> None: ...
    @abstractmethod
    def predict_proba(self, text: str) -> float: ...
