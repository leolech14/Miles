#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from miles.scheduler import setup_scheduler
from miles.source_search import update_sources

import bonus_alert_bot as bot
import yaml
import requests
from urllib.parse import urlparse
from typing import Any


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the scan and reply with any found promotions."""
    if not update.message or not update.effective_chat:
        return
    await update.message.reply_text("Scanning, please wait...")
    alerts = await asyncio.to_thread(bot.run_scan, str(update.effective_chat.id))
    if not alerts:
        await update.message.reply_text("No promos found.")
        return


def _diagnose_sources() -> list[str]:
    """Return a list of formatted source status lines."""
    path = os.getenv("SOURCES_PATH", "sources.yaml")
    try:
        with open(path) as f:
            urls: list[str] = yaml.safe_load(f)
    except Exception:
        return []
    results = []
    for url in urls:
        name = urlparse(url).netloc
        try:
            r = requests.head(
                url, headers=bot.HEADERS, timeout=10, allow_redirects=True
            )
            if r.status_code >= 400:
                raise ValueError(r.status_code)
        except Exception:
            results.append(f"\u274c {name} - {url}")
        else:
            results.append(f"\u2705 {name} - {url}")
    return results


async def sources(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Report which sources are responding."""
    if not update.message:
        return
    await update.message.reply_text("Checking sources, please wait...")
    lines = await asyncio.to_thread(_diagnose_sources)
    if not lines:
        await update.message.reply_text("No sources found.")
        return
    await update.message.reply_text("\n".join(lines))


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
    app.add_handler(CommandHandler("sources", sources))
    app.add_handler(CommandHandler("update", update))
    app.add_handler(CommandHandler("chat", chat))
    app.run_polling()


if __name__ == "__main__":
    main()
