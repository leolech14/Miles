#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from miles.scheduler import setup_scheduler

import bonus_alert_bot as bot
import yaml
import requests
from urllib.parse import urlparse


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


async def _post_init(app: object) -> None:
    setup_scheduler()


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    app = ApplicationBuilder().token(token).post_init(_post_init).build()
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("sources", sources))
    app.run_polling()


if __name__ == "__main__":
    main()
