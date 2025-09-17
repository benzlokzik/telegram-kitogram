# Telegram Admin Bot

A Telegram bot that automatically detects and removes bot-generated messages using machine learning spam detection.

## Features

- **Automatic Bot Detection**: Uses a pre-trained FastText model to detect bot-generated messages with >95% accuracy
- **Message Deletion**: Automatically deletes messages identified as bot-generated
- **SQLite Logging**: Records all detected bot messages in a local database
- **Statistics**: View detection statistics and recent activity
- **Commands**: 
  - `/start` - Start the bot
  - `/stats` - View detection statistics  
  - `/recent` - View recent detections

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

3. **Set Environment Variable**:
   ```bash
   export TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

4. **Run the Bot**:
   ```bash
   python main.py bot
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

The model was trained on Russian/English spam detection datasets and achieves high accuracy in distinguishing between human and bot-generated content.
