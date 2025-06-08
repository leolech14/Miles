#!/usr/bin/env python3
"""Bonus Alert Bot
===================

Monitor official mileage program pages for point transfer bonuses and alert a
Telegram chat when a new promotion is detected.
"""
from __future__ import annotations

import asyncio
from typing import Final, List

import redis
import aiohttp
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    Application,
    ApplicationBuilder,
    CallbackContext,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

# Update the import path if config.py is in a subdirectory, e.g.:
# from .config import get_settings
# Or, if config.py does not exist, create it with a get_settings function.
from config import get_settings
from miles.logging_config import setup_logging


logger = setup_logging().getChild(__name__)

# ───────────────────────── Redis helpers ─────────────────────────
_SETTINGS = get_settings()
_R: Final = redis.from_url(_SETTINGS.redis_url, decode_responses=True)

KEY_GPT_CHAT = "miles:gpt_mode:{chat_id}"  # per-chat toggle
KEY_GPT_GLOBAL = "miles:gpt_mode:global"  # global toggle (0 / 1)
KEY_MAX_TOKENS = "miles:openai:max_tokens"  # int


def _chat_enabled(chat_id: int) -> bool:
    global_flag = _R.get(KEY_GPT_GLOBAL) == "1"
    local_flag = _R.get(KEY_GPT_CHAT.format(chat_id=chat_id)) == "1"
    return global_flag or local_flag


# ───────────────────────── GPT toggles ──────────────────────────
async def _toggle_chat(chat_id: int, enabled: bool) -> None:
    if enabled:
        _R.set(KEY_GPT_CHAT.format(chat_id=chat_id), "1")
    else:
        _R.delete(KEY_GPT_CHAT.format(chat_id=chat_id))


async def gpt_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _toggle_chat(update.effective_chat.id, True)
    await update.effective_message.reply_text("🤖 GPT chat mode is ON.")


async def gpt_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _toggle_chat(update.effective_chat.id, False)
    await update.effective_message.reply_text("🛑 GPT chat mode is OFF.")


async def gpt_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /gpt-global-on and /gpt-global-off"""
    enable = update.message.text.endswith("on")
    _R.set(KEY_GPT_GLOBAL, "1" if enable else "0")
    state = "ON" if enable else "OFF"
    await update.effective_message.reply_text(f"🌐 GPT GLOBAL mode {state}")


# ───────────────────────── OpenAI settings ──────────────────────
async def set_max_tokens(update: Update, context: CallbackContext) -> None:
    if not context.args:
        await update.message.reply_text("Usage: /setmaxtokens <100-4096>")
        return
    try:
        n = int(context.args[0])
    except ValueError:
        await update.message.reply_text("Must be an integer.")
        return
    if not 100 <= n <= 4096:  # inclusive upper bound fixed
        await update.message.reply_text("Value must be 100-4096.")
        return
    _R.set(KEY_MAX_TOKENS, str(n))
    await update.message.reply_text(f"✅ Max tokens set to {n}")


# ───────────────────────── Diagnostics ──────────────────────────
async def diag(update: Update, _: CallbackContext) -> None:
    """Ping OpenAI and Redis; return status."""
    async with aiohttp.ClientSession() as sess:
        try:
            async with sess.get("https://api.openai.com/v1/models", timeout=8) as r:
                ok = r.status == 200
        except Exception as exc:  # noqa: BLE001
            ok = False
            logger.exception("OpenAI ping failed: %s", exc)
    redis_ok = True
    try:
        _R.ping()
    except redis.RedisError:
        redis_ok = False
    await update.message.reply_text(
        f"🔧 Diagnostics\n• OpenAI API: {'OK ✅' if ok else 'FAIL ❌'}\n"
        f"• Redis: {'OK ✅' if redis_ok else 'FAIL ❌'}"
    )


# ───────────────────────── Text handler ─────────────────────────
async def call_gpt(prompt: str, max_tokens: int = 1000) -> str:
    # Dummy implementation; replace with actual OpenAI API call as needed
    return f"Echo: {prompt[:max_tokens]}"

async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _chat_enabled(update.effective_chat.id):
        return
    prompt = (update.effective_message.text or "").strip()
    if not prompt:
        return
    try:
        await update.effective_chat.send_action(action="typing")
        max_tok = int(_R.get(KEY_MAX_TOKENS) or 1000)
        answer = await call_gpt(prompt, max_tokens=max_tok)
        await update.effective_message.reply_text(answer, parse_mode=ParseMode.MARKDOWN)
    except Exception:  # noqa: BLE001
        logger.exception("GPT call failed")
        await update.effective_message.reply_text("⚠️ LLM unavailable.")


# ───────────────────────── Dynamic /config ──────────────────────
async def config_cmd(update: Update, context: CallbackContext) -> None:
    chat_id = update.effective_chat.id
    gpt_state = "ON ✅" if _chat_enabled(chat_id) else "OFF ❌"
    max_tok = _R.get(KEY_MAX_TOKENS) or "1000 (default)"
    # ⬇︎ build list from dispatcher so it never goes stale
    app: Application = context.application
    lines: List[str] = [
        "<b>🤖 Current Configuration</b>",
        "",
        "<b>OpenAI</b>",
        f"• GPT per-chat: <b>{gpt_state}</b>",
        f"• Max Tokens: <b>{max_tok}</b>",
        "",
        "<b>Available Commands</b>",
    ]
    for cmd in sorted(app.commands):  # auto-populate!
        if cmd.startswith("_"):  # internal
            continue
        lines.append(f"• /{cmd}")
    await update.message.reply_text(
        "\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True
    )


# ───────────────────────── Build application ────────────────────
def build_app() -> Application:
    builder = (
        ApplicationBuilder()
        .token(_SETTINGS.telegram_token)
        .rate_limiter(AIORateLimiter())
    )
    app = builder.build()

    # GPT toggles
    app.add_handler(CommandHandler(["gpt-on", "gpt_on"], gpt_on))
    app.add_handler(CommandHandler(["gpt-off", "gpt_off"], gpt_off))
    app.add_handler(CommandHandler(["gpt-global-on"], gpt_global))
    app.add_handler(CommandHandler(["gpt-global-off"], gpt_global))

    # Settings
    app.add_handler(CommandHandler(["setmaxtokens", "set-max-tokens"], set_max_tokens))
    app.add_handler(CommandHandler(["config", "help"], config_cmd))
    app.add_handler(CommandHandler("diag", diag))

    # Catch-all text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


# ───────────────────────── Entrypoint ───────────────────────────
async def main() -> None:
    app = build_app()
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
