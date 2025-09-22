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

- **Automatic Bot Detection**: Uses a pre-trained FastText model to detect bot-generated messages with >95% accuracy
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
2. Each message is analyzed using a FastText spam detection model
3. If the spam probability is >95%, the message is considered bot-generated
4. Bot messages are automatically deleted and logged to a SQLite database
5. Admins can view statistics and recent activity using bot commands

## Setup

1. **Get a Bot Token**:
   - Message @BotFather on Telegram
   - Create a new bot with `/newbot`
   - Save the token provided

2. **Install Dependencies**:
   ```bash
   pip install uv
   uv sync
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
   python main.py
   ```

## Testing

Run the test suite to verify functionality:

```bash
python test_bot.py
```

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

Uses a pre-trained FastText model for spam detection located at:
`dialogue_kitogram/data/antispam.bin`
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

The model was trained on Russian/English spam detection datasets and achieves high accuracy in distinguishing between human and bot-generated content.
