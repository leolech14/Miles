#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from miles.scheduler import setup_scheduler
from miles.source_search import update_sources
from miles.source_store import SourceStore

import bonus_alert_bot as bot
from typing import Any

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


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reply using OpenAI ChatCompletion."""
    if not update.message:
        return
    text = update.message.text or ""
    parts = text.split(" ", 1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /chat <message>")
        return
    await update.message.reply_text("Thinking...")
    try:
        import openai

        openai.api_key = os.getenv("OPENAI_API_KEY")
        resp: Any = await asyncio.to_thread(
            openai.ChatCompletion.create,
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": parts[1]}],
        )
        msg = resp["choices"][0]["message"]["content"].strip()
    except Exception as e:  # pragma: no cover - network usage
        await update.message.reply_text(f"Error: {e}")
        return
    await update.message.reply_text(msg)


async def _post_init(app: object) -> None:
    setup_scheduler()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    app = ApplicationBuilder().token(token).post_init(_post_init).build()
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("sources", handle_sources))
    app.add_handler(CommandHandler("addsrc", handle_addsrc))
    app.add_handler(CommandHandler("rmsrc", handle_rmsrc))
    app.add_handler(CommandHandler("update", update))
    app.add_handler(CommandHandler("chat", chat))
    app.run_polling()


if __name__ == "__main__":
    main()
