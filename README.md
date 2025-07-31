# Crypto Bot - Automated Short Trading

This project implements an automated trading bot for short positions on cryptocurrency pairs (e.g., SOL/USDT) using the Bitget API. The bot detects high-probability short opportunities based on technical conditions and executes trades automatically.

## Features

- **Real-time market monitoring** via Bitget API (3-minute candles)
- **Entry conditions**:
  - Price surge of +12% in 30 minutes
  - Volume > 2.5x average over last 10 candles
  - RSI(5) > 80 and declining
  - EMA9 trending downward
  - Strong bearish rejection (wick ratio > 0.7)
- **Risk management**:
  - Position size: $1 (configurable)
  - Leverage: x20 (configurable)
  - Stop loss: 5% above entry
  - Partial take profit at +7%
  - Trailing stop at +3.5%
  - 5-minute cooldown between trades
- **Telegram notifications** for all actions (entry, TP, SL)
- **Auto-restart** on failure

## Setup

1. Create a GitHub repository and add the files below
2. Deploy to Railway from GitHub
3. Add environment variables in Railway settings
4. Start the bot

## Files

- `main.py`: Core bot logic
- `requirements.txt`: Required Python packages
- `Procfile`: Deployment configuration

## Environment Variables

| Variable | Description |
|---------|-------------|
| `BITGET_API_KEY` | Your Bitget API key |
| `BITGET_SECRET` | Your Bitget secret |
| `BITGET_PASSWORD` | Your Bitget password |
| `TELEGRAM_TOKEN` | Telegram bot token |
| `TELEGRAM_CHAT_ID` | Your Telegram chat ID |
| `SYMBOL` | Trading pair (default: SOL/USDT:USDT) |
| `LEVERAGE` | Leverage (default: 20) |
| `POSITION_SIZE` | Trade size in USD (default: 1) |

## Usage

The bot runs continuously and checks for trade signals every 10 seconds. When conditions are met, it opens a short position with the specified parameters.

> ⚠️ **Warning**: This bot uses high leverage (x20). Use only with funds you can afford to lose.
