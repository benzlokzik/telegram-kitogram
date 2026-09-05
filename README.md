# Dialog Kitogram

Dialogue management KIT bot for Telegram using.

Currently supports:

- Automatic detection and removal of bot-generated messages using machine learning spam detection.
- SQLite logging of all detected bot messages.
- Statistics and recent activity view.
- Commands:
  - `/start` - Start the bot
  - `/stats` - View detection statistics  
  - `/recent` - View recent detections
  - `/allow` - Allow a chat for moderation
  - `/disallow` - Remove a chat from moderation
  - `/allowed` - View allowed chats
  - `/del` - Admin-only. Reply to a message to delete it manually

## Features

- **Automatic Bot Detection**: Uses the pre-trained BERT transformer from spam-detector v0.2.0 (rubert-tiny2)
- **Message Deletion**: Automatically deletes messages identified as bot-generated
- **SQLite Logging**: Records all detected bot messages in a local database
- **Statistics**: View detection statistics and recent activity
- **Commands**: 
  - `/start` - Start the bot
  - `/stats` - View detection statistics  
  - `/recent` - View recent detections
  - `/del` - Admin-only, reply-based manual deletion

## How It Works

1. The bot monitors all text messages in the chat
2. Each message is analyzed using BERT in a dedicated worker, keeping Telegram handlers responsive; polling handles at most 32 updates concurrently to bound the inference queue
3. The adjusted spam score is compared with `SPAM_THRESHOLD` (default `0.95`)
4. Bot messages are automatically deleted and logged to a SQLite database
5. Admins can view statistics and recent activity using bot commands

The existing score adjustments are preserved: subtract `0.1` for a newline and
`0.1` for more than five words. At the default threshold, either adjustment
prevents automatic deletion even when the model returns `1.0`. The threshold is
a moderation setting, not a measured accuracy figure.

## Setup

1. **Get a Bot Token**:
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Save the token provided

2. **Install Dependencies**:
   ```bash
   pip install uv
   uv sync --locked --no-dev --python 3.12
   ```

3. **Configure Environment**:
   ```bash
   # Copy the example configuration file
   cp .env.example .env
   
   # Edit .env file and set your bot token
   # TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```
   
   Alternatively, set environment variables directly:
   ```bash
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   export SPAM_THRESHOLD=0.95
   ```

4. **Run the Bot**:
   ```bash
   # Starts the bot by default
   uv run --locked --no-dev python main.py
   ```

## Testing

Run offline integration and moderation tests (no Telegram calls or model downloads):

```bash
uv run --locked --no-dev python -m unittest discover -s tests -v
```

Run a smoke check with the real transformer weights and a temporary SQLite database:

```bash
uv run --locked --no-dev python test_bot.py
```

The first smoke run downloads the model. Both commands must exit with status `0`;
the smoke check prints `All tests passed!` and fails on invalid probabilities or
model/database errors. These examples do not measure classification accuracy.

## Bot Permissions

The bot requires the following permissions in your Telegram group:
- Delete messages
- Read messages

## Database

The bot creates a local SQLite database (`bot_messages.db`) to store:
- Message ID and chat information
- User details (ID, username)
- Message content
- Spam probability score
- Detection timestamp
- Whether the message was successfully deleted

## Model

The runtime uses `BertSpamModel` from
[`spam-detector[transformers]` v0.2.0](https://github.com/benzlokzik/spam-detector/releases/tag/v0.2.0),
locked to commit `00b0474db3e79556d8d951f1287801f1ccdc06b4` in `uv.lock`.
It loads the trained Russian-language
[`benzlokzik/spam-detector-bert`](https://huggingface.co/benzlokzik/spam-detector-bert)
weights, pinned to revision `3dd73bd4dcff411d44e1bc1a8e90d0568ca04395`.

- `SPAM_MODEL_ID` and `SPAM_MODEL_REVISION` override the repository and revision;
  change both together when switching repositories.
- The first startup downloads approximately 117 MB of weights plus tokenizer files.
  Subsequent starts reuse the Hugging Face cache (`HF_HOME` can override its location).
  With a complete cache, `HF_HUB_OFFLINE=1` prevents Hub network requests.
- Loading failure stops startup. There is no automatic fallback to FastText.
- Upstream inference truncates text to 128 tokens and returns the probability of
  class `1` (spam). GPU selection is automatic when available; Linux dependencies
  use the CPU-only PyTorch index for the droplet.
- The legacy FastText code and training files remain available for experiments:
  `uv sync --locked --group fasttext`. They are not used by the bot. Training data
  are excluded from the runtime image.

## Docker deployment

After review approval, update the server checkout to the approved commit. Keep its
existing `.env`, `bot_messages.db`, and `logs/`; no database migration is required.
On a fresh installation, create the database file with `touch bot_messages.db`
before starting Compose so the bind mount is a file.

```bash
docker compose build bot
# Download/cache and load BERT before replacing the running bot.
docker compose run --rm --no-deps bot /app/.venv/bin/python -c \
  'from dialogue_kitogram.src.spam_model import load_spam_model; print(load_spam_model().predict_proba("Привет! Как дела?"))'
docker compose up -d --no-deps bot
docker compose ps
docker compose logs --tail=100 bot
```

The preflight must exit `0` and print a probability in `[0, 1]`. Startup logs must
show `BERT spam model loaded` and `Starting bot...`, with no restart loop. The
`model-cache` named volume preserves downloaded weights across container rebuilds;
keep it when stopping the stack. Reserve memory for PyTorch and the transformer
in addition to the bot, and verify actual memory use on the target droplet.

## Admins and Allowed Chats

- Set admin Telegram user IDs via environment variable:
  ```bash
  export ADMIN_USER_IDS="123456789,987654321"
  ```
  Supports comma or space separated integers.

- Only chats in the allow-list are moderated. Admins can manage it:
  - In a group (as admin): `/allow` to allow current chat
  - In a group: `/disallow` to remove current chat
  - In a group: reply to a message with `/del` to delete it (admins only)
  - In a DM with the bot (admin only):
    - `/allow <chat_id> [title]`
    - `/disallow <chat_id>`
    - `/allowed` — list allowed chats

Non-admin DMs receive a brief notice to contact an admin.
