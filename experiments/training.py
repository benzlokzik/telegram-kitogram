import marimo

__generated_with = "0.15.5"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    import pandas as pd
    return mo, pd


@app.cell
def _():
    from dialogue_kitogram.src.fastspam.ft_model import FastTextSpamModel, ModelConfig
    return FastTextSpamModel, ModelConfig


@app.cell
def _(FastTextSpamModel, ModelConfig):
    cfg = ModelConfig()
    FastTextSpamModel(cfg)
    return (cfg,)


@app.cell
def _(FastTextSpamModel, cfg, mo, pd):
    def predict(text: str):
        model = FastTextSpamModel(cfg)
        labels, probs = model.predict_proba(text)
        return mo.Html(
            pd.DataFrame(
                {
                    "Label": labels,
                    "Probability": [
                        f"{p:.4f}" for p in probs
                    ],  # format floats to 4 decimals
                },
            ).to_html(index=False),
        )
    return (predict,)


@app.cell
def _(predict):
    # predict("хуй тебе")
    predict("хуй тебе, а не пизда")
    return


@app.cell
def _(pd):
    df = pd.read_parquet(
        "hf://datasets/alt-gnome/telegram-spam/data/train-00000-of-00001.parquet",
    )

    df["text"] = df.apply(
        lambda row: "__label_ham " + row["text"]
        if row["label"] == 0
        else "__label_spam " + row["text"],
        axis=1,
    )
    return (df,)


@app.cell
def _(df):
    df
    return


@app.cell
def _(df):
    df["text"].to_csv(
        "./dialogue_kitogram/data/labeled_dataset_from_hf.txt",
        index=False,
        header=False,
    )
    return


@app.cell
def _(cfg):
    cfg.train_names = ["train_data.txt", "labeled_dataset_from_hf.txt"]
    return


@app.cell
def _(mo):
    button = mo.ui.run_button()
    button
    return (button,)


@app.cell
def _(FastTextSpamModel, button, cfg, mo):
    mo.stop(button.value, mo.md("Click the button to retrain the model"))

    FastTextSpamModel(cfg).fit()
    return


@app.cell
def _(predict):
    predict("хуй тебе, а не пизда")
    return


@app.cell
def _(predict):
    predict(
        "У тебя есть переменная, у которой значение float('inf'), это буквально ∞, ты пытаешься ее сконвертировать в int",
    )
    return


@app.cell
def _(predict):
    predict(
        "Я желаю удалить ваше сотрудничество с рекламой, заплатят когда удалю полностью? И сколько?",
    )
    return


@app.cell
def _(predict):
    predict("Вам платят?")
    return


@app.cell
def _(predict):
    predict("qq")
    return


@app.cell
def _(predict):
    predict("добро пожаловать аахах")
    return


@app.cell
def _(predict):
    predict("ахахахаа")
    return


@app.cell
def _(predict):
    predict("здравстуйте. знаю, что не теме, но у меня есть инетересная вакансия")
    return


@app.cell
def _(predict):
    predict("бля я крч вакансию нашел недавно")
    return


if __name__ == "__main__":
    app.run()
