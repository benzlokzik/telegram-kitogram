import fasttext

try:
    from src.core.base_model import ModelConfig, SpamModel
except ImportError:
    # Fallback for when running as script
    import sys
    from pathlib import Path

    sys.path.append(str(Path(__file__).parent.parent))
    from core.base_model import ModelConfig, SpamModel


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

    def _validate_training_file(self) -> None:
        train_path = self.cfg.train_path
        if not train_path.exists():
            msg = f"Training file not found: {train_path}"
            raise FileNotFoundError(msg)
        # FastText expects lines like: "__label__spam text ..." or "__label__ham text ..."
        # We ensure at least one line starts with the label prefix.
        with train_path.open("r", encoding="utf-8") as f:
            has_labelled_line = any(line.lstrip().startswith("__label__") for line in f)
        if not has_labelled_line:
            msg = (
                "Training data must be labelled in FastText format, for example: \n"
                "__label__spam Your text here\n"
                "__label__ham Your text here"
            )
            raise ValueError(msg)

    def fit(self) -> None:
        print("Training FastText model...")
        print(f"Training data path: {self.cfg.train_path}")
        self._validate_training_file()
        m = fasttext.train_supervised(input=str(self.cfg.train_path), **self.params)
        if self.quantize:
            m.quantize(
                input=str(self.cfg.train_path),
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
        labels, probs = model.predict(text.lower().strip(), k=2)
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
