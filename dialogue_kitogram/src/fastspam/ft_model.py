import pathlib
import shutil
from tempfile import NamedTemporaryFile

import fasttext

from ..core.base_model import ModelConfig, SpamModel


class FastTextSpamModel(SpamModel):
    def __init__(
        self,
        cfg: ModelConfig,
        dim=64,
        lr=0.5,
        epoch=25,
        wordNgrams=2,
        minn=2,
        maxn=4,
        loss="ova",
        quantize=True,
        qnorm=True,
        retrain=True,
        cutoff=100000,
    ) -> None:
        super().__init__(cfg)
        self.params = {
            "dim": dim,
            "lr": lr,
            "epoch": epoch,
            "wordNgrams": wordNgrams,
            "minn": minn,
            "maxn": maxn,
            "loss": loss,
        }
        self.quantize = quantize
        self.qnorm = qnorm
        self.retrain = retrain
        self.cutoff = cutoff
        self._m: fasttext.FastText._FastText | None = None

    def _validate_training_files(self, paths: list[pathlib.Path]) -> None:
        if not paths:
            msg = "No training files provided"
            raise FileNotFoundError(msg)
        for path in paths:
            if not path.exists():
                msg = f"Training file not found: {path}"
                raise FileNotFoundError(msg)
            with path.open("r", encoding="utf-8") as f:
                has_labelled_line = any(
                    line.lstrip().startswith("__label__") for line in f
                )
            if not has_labelled_line:
                msg = (
                    f"Training data in {path} must be labelled in FastText format,\n"
                    "e.g.:\n__label__spam Your text here\n__label__ham Your text here"
                )
                raise ValueError(msg)

    def fit(self) -> None:
        print("Training FastText model...")
        paths = self.cfg.train_paths()
        self._validate_training_files(paths)
        # Merge multiple files into a temporary file to feed FastText
        with NamedTemporaryFile(mode="w+", delete=False, encoding="utf-8") as tmp:
            tmp_path = tmp.name
            for p in paths:
                with p.open("r", encoding="utf-8") as f:
                    shutil.copyfileobj(f, tmp)
            tmp.flush()
        input_path = pathlib.Path(tmp_path)

        print("Training data files:", [str(p) for p in paths])
        m = fasttext.train_supervised(input=str(input_path), **self.params)
        if self.quantize:
            m.quantize(
                input=str(input_path),
                qnorm=self.qnorm,
                retrain=self.retrain,
                cutoff=self.cutoff,
            )
        m.save_model(str(self.cfg.model_path))
        self._m = m

    def load(self) -> None:
        self._m = fasttext.load_model(str(self.cfg.model_path))

    def predict_proba(self, text: str) -> float:
        if self._m is None:
            self.load()
        model = self._m
        if model is None:
            msg = "Model is not loaded"
            raise RuntimeError(msg)
        labels, probs = model.predict(text.lower().replace("\n", "\t").strip(), k=2)
        # return (labels, probs)
        return max(
            (p for l, p in zip(labels, probs, strict=False) if l == "__label__spam"),
            default=0.0,
        )


if __name__ == "__main__":
    cfg = ModelConfig()
    model = FastTextSpamModel(cfg)
    model.fit()
    print(
        model.predict_proba("Срочно работа в Москве! З/п 150 000 руб! Писать на в лс"),
    )
    print(
        model.predict_proba(
            "блять как же заебали кустовые эйдоры сука ненавижу их всех",
        ),
    )
    print(
        model.predict_proba(
            "qq",
        ),
    )
