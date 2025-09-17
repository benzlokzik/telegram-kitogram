import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for spam detection model paths."""

    project_root: pathlib.Path = pathlib.Path(__file__).resolve().parents[3]
    data_subdir: str = "dialogue_kitogram/data"
    model_name: str = "antispam.bin"
    train_name: str = "train_data.txt"
    train_names: list[str] | None = None

    @property
    def data_dir(self) -> pathlib.Path:
        return self.project_root / self.data_subdir

    @property
    def model_path(self) -> pathlib.Path:
        return self.data_dir / self.model_name

    @property
    def train_path(self) -> pathlib.Path:
        return (self.data_dir / self.train_name).absolute()

    def train_paths(self) -> list[pathlib.Path]:
        """Return one or more training file paths.

        - If `train_names` is provided, resolve each name to an absolute Path.
        - Otherwise, return a single-element list with `train_path`.
        """
        if self.train_names:
            resolved: list[pathlib.Path] = []
            for name in self.train_names:
                p = pathlib.Path(name)
                if not p.is_absolute():
                    p = self.data_dir / name
                resolved.append(p.absolute())
            return resolved
        return [self.train_path]


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
