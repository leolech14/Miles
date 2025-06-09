#!/usr/bin/env python3
"""
Natural Language Miles Bot

A conversational AI assistant that feels like ChatGPT but with all the
Miles bot functionalities. Uses OpenAI function calling to replace
command-based interactions with natural language.
"""

from __future__ import annotations

import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from miles.logging_config import setup_logging
from miles.natural_language.conversation_manager import conversation_manager
from miles.scheduler import setup_scheduler

logger = setup_logging().getChild(__name__)

print("[natural_language_bot] Starting Natural Language Miles Bot...")
print(f"[natural_language_bot] Python version: {__import__('sys').version}")
print(f"[natural_language_bot] Working directory: {os.getcwd()}")
print(
    f"[natural_language_bot] TELEGRAM_BOT_TOKEN set: {'TELEGRAM_BOT_TOKEN' in os.environ}"
)
print(f"[natural_language_bot] OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
print(f"[natural_language_bot] REDIS_URL: {os.getenv('REDIS_URL', 'NOT_SET')}")

REQUIRED_ENV_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "OPENAI_API_KEY",  # Now required for natural language
]

OPTIONAL_ENV_VARS = [
    "REDIS_URL",  # Falls back to file storage
    "MIN_BONUS",  # Has default value
    "LOG_WEBHOOK_URL",  # Optional logging
]


def check_environment_variables() -> None:
    """Check required environment variables and exit if missing."""
    print(
        f"[natural_language_bot] Checking required environment variables: {', '.join(REQUIRED_ENV_VARS)}"
    )
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(
            f"[natural_language_bot] ERROR: Missing required environment variables: {', '.join(missing)}"
        )
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    print("[natural_language_bot] All required environment variables are set")

    # STRICT VALIDATION: Check OPENAI_API_KEY is not a zombie value
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key in {"not_set", "dummy", "placeholder"}:
        print(
            f"[natural_language_bot] 🚫 OPENAI_API_KEY has invalid zombie value: '{openai_key}'"
        )
        print("[natural_language_bot] To fix:")
        print("[natural_language_bot]   fly secrets set OPENAI_API_KEY=sk-proj-...")
        print("[natural_language_bot]   gh secret set OPENAI_API_KEY -b'sk-proj-...'")
        raise SystemExit("OPENAI_API_KEY contains invalid placeholder value")

    # Check optional variables and warn if missing
    print(
        f"[natural_language_bot] Checking optional environment variables: {', '.join(OPTIONAL_ENV_VARS)}"
    )
    missing_optional = [var for var in OPTIONAL_ENV_VARS if not os.getenv(var)]
    if missing_optional:
        print(
            f"[natural_language_bot] WARNING: Missing optional environment variables: {', '.join(missing_optional)}"
        )
        print("[natural_language_bot] Some features may be degraded:")
        for var in missing_optional:
            if var == "REDIS_URL":
                print("[natural_language_bot] - Using file storage instead of Redis")
            elif var == "MIN_BONUS":
                print("[natural_language_bot] - Using default minimum bonus threshold")
            elif var == "LOG_WEBHOOK_URL":
                print("[natural_language_bot] - CI log streaming disabled")
    else:
        print("[natural_language_bot] All optional environment variables are set")


async def handle_text_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle all text messages through natural language processing."""
    await conversation_manager.handle_message(update, context)


async def handle_image_message(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle image messages with multimodal AI."""
    await conversation_manager.handle_image_message(update, context)


async def handle_reset_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /reset command to clear conversation."""
    if not update.effective_user:
        return

    conversation_manager.clear_conversation(update.effective_user.id)
    if update.message:
        await update.message.reply_text(
            "🔄 Conversation cleared! Hi, I'm Miles, your Brazilian mileage assistant. "
            "How can I help you find the best transfer bonuses today?"
        )


async def handle_help_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /help command with natural language guidance."""
    if not update.message:
        return

    help_text = """🤖 **Miles - Natural Language Assistant**

I'm Miles, your intelligent Brazilian mileage monitoring assistant! Instead of using commands, just talk to me naturally like you would with ChatGPT.

🎯 **What I can help you with:**
• Find current transfer bonus promotions
• Manage your monitored sources
• Discover new mileage websites
• Configure scan schedules
• Analyze performance and optimize settings
• Answer questions about mileage programs

💬 **Example conversations:**
• "Are there any good bonuses today?"
• "Add this website to monitor: https://example.com"
• "Check for bonuses every 4 hours"
• "Show me all my sources"
• "Find new mileage websites"
• "What's the best time to scan for bonuses?"

🖼️ **Multimodal support:**
Send me images of promotions or mileage program pages and I'll analyze them for you!

🔄 **Special commands:**
• `/reset` - Clear our conversation and start fresh
• `/help` - Show this help message

Just start chatting naturally - I understand Portuguese and English! 🇧🇷🇺🇸"""

    await update.message.reply_text(help_text, parse_mode="Markdown")


async def handle_start_command(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handle /start command with welcoming message."""
    if not update.message:
        return

    welcome_text = """🚀 **Welcome to Miles - Natural Language Edition!**

Olá! I'm Miles, your intelligent Brazilian mileage assistant. I monitor 50+ sources for transfer bonus promotions and help you never miss a great deal!

🧠 **What makes me special:**
• Natural conversation - just talk to me like ChatGPT
• Real-time promotion scanning across all major programs
• AI-powered source discovery
• Intelligent scheduling and optimization
• Multimodal support - send me images too!

💬 **Get started by asking:**
• "What bonuses are available right now?"
• "Help me set up monitoring"
• "Find the best Livelo promotions"

I'm here to help you maximize your mileage strategy! What would you like to know? ✈️"""

    await update.message.reply_text(welcome_text, parse_mode="Markdown")


class HealthHandler(BaseHTTPRequestHandler):
    """Health check handler for monitoring."""

    def do_GET(self) -> None:
        if self.path == "/metrics":
            self._handle_metrics()
        elif self.path == "/health":
            self._handle_health()
        else:
            self._handle_health()

    def _handle_health(self) -> None:
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"OK - Natural Language Miles Bot")

    def _handle_metrics(self) -> None:
        try:
            from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

            from miles.metrics import get_metrics_registry, record_memory_usage

            # Update dynamic metrics
            record_memory_usage()

            # Generate metrics
            metrics_data = generate_latest(get_metrics_registry())

            self.send_response(200)
            self.send_header("Content-Type", CONTENT_TYPE_LATEST)
            self.end_headers()
            self.wfile.write(metrics_data)
        except Exception as e:
            self.send_response(500)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(f"Error generating metrics: {e!s}".encode())


def start_health_server() -> None:
    """Start health check server on port 8080."""
    server = HTTPServer(("127.0.0.1", 8080), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    logger.info("Health server started on :8080")


async def post_init(app: object) -> None:
    """Post-initialization setup."""
    try:
        print("[natural_language_bot] Setting up scheduler...")
        setup_scheduler()
        print("[natural_language_bot] Scheduler setup complete")
    except Exception as e:
        print(f"[natural_language_bot] Scheduler setup failed: {e}")
        import traceback

        traceback.print_exc()


def build_app() -> object:
    """Build the Telegram application."""
    builder = ApplicationBuilder().token(os.getenv("TELEGRAM_BOT_TOKEN"))
    app = builder.build()

    # Command handlers
    app.add_handler(CommandHandler("start", handle_start_command))
    app.add_handler(CommandHandler("help", handle_help_command))
    app.add_handler(CommandHandler("reset", handle_reset_command))

    # Message handlers (natural language)
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message)
    )
    app.add_handler(MessageHandler(filters.PHOTO, handle_image_message))

    # Post-initialization
    app.post_init = post_init

    return app


def main() -> None:
    """Main entry point."""
    print("[natural_language_bot] Starting main function...")

    try:
        # Check environment
        check_environment_variables()
        print("[natural_language_bot] ✅ Environment validation passed")

        # Start health server
        start_health_server()

        # Build and run app
        app = build_app()
        print("[natural_language_bot] ✅ Telegram application built successfully")

        print("[natural_language_bot] 🚀 Starting Natural Language Miles Bot...")
        print(
            "[natural_language_bot] Bot is now running with natural language interface!"
        )
        print(
            "[natural_language_bot] Users can chat naturally instead of using commands"
        )

        # Run the bot
        app.run_polling(drop_pending_updates=True)

    except KeyboardInterrupt:
        print("[natural_language_bot] Bot stopped by user")
    except Exception as e:
        print(f"[natural_language_bot] ❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
