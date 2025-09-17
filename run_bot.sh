#!/bin/bash

# Demo script for the Telegram Admin Bot
# This shows how to set up and run the bot

echo "🤖 Telegram Admin Bot Demo Setup"
echo "================================"
echo

# Check if token is provided
if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
    echo "❌ TELEGRAM_BOT_TOKEN environment variable not set"
    echo
    echo "To get a bot token:"
    echo "1. Message @BotFather on Telegram"
    echo "2. Send /newbot command"
    echo "3. Follow instructions to create your bot"
    echo "4. Copy the token and set it:"
    echo "   export TELEGRAM_BOT_TOKEN=your_token_here"
    echo
    echo "Then run this script again."
    exit 1
fi

echo "✅ Bot token found"
echo

# Install dependencies
echo "📦 Installing dependencies..."
if command -v uv &> /dev/null; then
    uv sync
else
    echo "Installing uv package manager..."
    pip install uv
    uv sync
fi

echo
echo "🧪 Running tests..."
python test_bot.py

echo
echo "🚀 Starting bot..."
echo "Bot will monitor messages and delete those with >95% spam probability"
echo "Press Ctrl+C to stop"
echo

python main.py bot