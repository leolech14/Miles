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

import bonus_alert_bot as bot
import yaml
import requests
from urllib.parse import urlparse

openai.api_key = os.getenv("OPENAI_API_KEY")
if not openai.api_key:
    logging.warning("OPENAI_API_KEY is not set; /chat may not work")
memory = ChatMemory()


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


def main() -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
    app = ApplicationBuilder().token(token).post_init(_post_init).build()
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("sources", sources))
    app.add_handler(CommandHandler("update", update))
    app.add_handler(CommandHandler("chat", handle_chat))
    app.add_handler(CommandHandler("end", handle_end))
    app.run_polling()


if __name__ == "__main__":
    main()
