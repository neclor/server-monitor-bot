# Server Monitor Bot

A Telegram bot that monitors server health (CPU, memory, disk, uptime, temperature) and sends periodic status updates.

## Running with Docker (recommended)

1. Copy `.env.example` to `.env` and fill in the values
2. Run: `docker compose up -d`

## Running locally

1. Copy `.env.example` to `.env` and fill in the values
2. Install dependencies: `pip install -r requirements.txt`
3. Run: `python -m src`

## Configuration

| Variable | Required | Default | Description |
|---|---|---|---|
| `TG_BOT_API_ID` | yes | — | Telegram API ID |
| `TG_BOT_API_HASH` | yes | — | Telegram API hash |
| `TG_BOT_TOKEN` | yes | — | Bot token |
| `TG_BOT_CHAT_ID` | yes | — | Chat ID to send messages to |
| `STATUS_UPDATE_START_DELAY` | no | `60` | Seconds before first auto-update |
| `STATUS_UPDATE_DELAY` | no | `600` | Seconds between auto-updates |

## Commands

| Command | Description |
|---|---|
| `/status` | Show current server status |
| `/help` | Show available commands |
