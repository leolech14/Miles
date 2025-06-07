#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import openai
from miles.chat_store import ChatMemory

from miles.scheduler import setup_scheduler
from miles.source_search import update_sources
from miles.source_store import SourceStore

import bonus_alert_bot as bot
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

print("[ask_bot] Starting up...")
print(f"[ask_bot] TELEGRAM_BOT_TOKEN set: {'TELEGRAM_BOT_TOKEN' in os.environ}")
print(f"[ask_bot] REDIS_URL: {os.getenv('REDIS_URL')}")
print(f"[ask_bot] OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")

REQUIRED_ENV_VARS = [
    "OPENAI_API_KEY",
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "REDIS_URL",
]
missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing:
    raise SystemExit(f"Missing required environment variables: {', '.join(missing)}")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY is missing. Please update your environment variables."
    )

openai.api_key = OPENAI_API_KEY
memory = ChatMemory()

store = SourceStore()


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the scan and reply with any found promotions."""
    if not update.message or not update.effective_chat:
        return
    await update.message.reply_text("Scanning, please wait...")
    alerts = await asyncio.to_thread(bot.run_scan, str(update.effective_chat.id))
    if not alerts:
        await update.message.reply_text("No promos found.")
        return


async def handle_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    lst = store.all()
    if not lst:
        await update.message.reply_text("⚠️  No sources configured.")
        return
    if len(lst) > 50:
        extra = len(lst) - 50
        lst = lst[:50]
        lines = [f"{i+1}. {u}" for i, u in enumerate(lst)]
        lines.append(f"… and {extra} more")
    else:
        lines = [f"{i+1}. {u}" for i, u in enumerate(lst)]
    await update.message.reply_text("\n".join(lines))


async def handle_addsrc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /addsrc <url>")
        return
    url = parts[1].strip()
    if store.add(url):
        await update.message.reply_text("✅ added.")
    else:
        await update.message.reply_text("Already present or invalid.")


async def handle_rmsrc(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /rmsrc <index|url>")
        return
    target = parts[1].strip()
    removed = store.remove(target)
    if removed:
        await update.message.reply_text(f"🗑️ removed: {removed}")
    else:
        await update.message.reply_text("Not found.")


async def update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for new sources and report the result."""
    if not update.message:
        return
    await update.message.reply_text("Updating sources, please wait...")
    added = await asyncio.to_thread(update_sources)
    if added:
        msg = "New sources added:\n" + "\n".join(added)
    else:
        msg = "No new sources found."
    await update.message.reply_text(msg)


async def handle_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /chat <message>")
        return
    user_id = update.effective_user.id
    user_msgs = memory.get(user_id)
    user_msgs.append({"role": "user", "content": parts[1]})

    try:
        resp = await asyncio.to_thread(
            openai.chat.completions.create,
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=user_msgs[-20:],
            stream=False,
            temperature=0.7,
        )
        reply = resp.choices[0].message.content
    except Exception as e:
        logging.exception("OpenAI call failed")
        await update.message.reply_text(f"Error: {e.__class__.__name__}: {e}")
        return

    user_msgs.append({"role": "assistant", "content": reply})
    memory.save(user_id, user_msgs[-20:])
    await update.message.reply_text(reply)


async def handle_end(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    memory.clear(update.effective_user.id)
    await update.message.reply_text("\u2702\ufe0f  Chat ended.")


async def _post_init(app: object) -> None:
    setup_scheduler()


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def start_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main() -> None:
    start_health_server()  # Start HTTP health server for Fly.io
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    app = ApplicationBuilder().token(token).post_init(_post_init).build()
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("sources", handle_sources))
    app.add_handler(CommandHandler("addsrc", handle_addsrc))
    app.add_handler(CommandHandler("rmsrc", handle_rmsrc))
    app.add_handler(CommandHandler("update", update))
    app.add_handler(CommandHandler("chat", handle_chat))
    app.add_handler(CommandHandler("end", handle_end))
    app.run_polling()


if __name__ == "__main__":
    main()
