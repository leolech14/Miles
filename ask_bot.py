#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

from miles.scheduler import setup_scheduler

import bonus_alert_bot as bot


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the scan and reply with any found promotions."""
    await update.message.reply_text("Scanning, please wait...")
    alerts = await asyncio.to_thread(bot.run_scan, update.effective_chat.id)
    if not alerts:
        await update.message.reply_text("No promos found.")
        return


async def _post_init(app: object) -> None:
    setup_scheduler()
    await asyncio.to_thread(bot.run_scan)


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = (
        ApplicationBuilder()
        .token(token)
        .post_init(_post_init)
        .build()
    )
    app.add_handler(CommandHandler("ask", ask))
    app.run_polling()


if __name__ == "__main__":
    main()
