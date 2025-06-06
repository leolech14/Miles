#!/bin/bash
# Convenience script to run both Telegram bots.
set -euo pipefail

if [[ -z "${TELEGRAM_BOT_TOKEN:-}" ]]; then
  echo "TELEGRAM_BOT_TOKEN not set" >&2
  exit 1
fi

if [[ -z "${TELEGRAM_CHAT_ID:-}" ]]; then
  echo "TELEGRAM_CHAT_ID not set" >&2
  exit 1
fi

python bonus_alert_bot.py &
MAIN_PID=$!
python ask_bot.py &
ASK_PID=$!

trap "kill $MAIN_PID $ASK_PID" SIGINT SIGTERM
wait $MAIN_PID $ASK_PID
