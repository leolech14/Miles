#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

import bonus_alert_bot as bot


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the scan and reply with any found promotions."""
    await update.message.reply_text("Scanning, please wait...")
    alerts = bot.run_scan()
    if not alerts:
        await update.message.reply_text("No promos found.")
        return
    for pct, src, link in alerts:
        msg = f"\U0001F4E3 {pct}% · {src}\n{link}"
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=msg,
            disable_web_page_preview=True,
        )


def main() -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("ask", ask))
    app.run_polling()


if __name__ == "__main__":
    main()
