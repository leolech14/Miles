#!/usr/bin/env python3
"""Bonus Alert Bot
===================

Monitor official mileage program pages for point transfer bonuses and alert a
Telegram chat when a new promotion is detected.
"""
from __future__ import annotations

import asyncio
import os
from typing import Final, List, Set, Tuple, Any

import redis
import aiohttp
import requests
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import (
    AIORateLimiter,
    ApplicationBuilder,
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
from miles.source_store import SourceStore
from miles.plugin_loader import discover_plugins


logger = setup_logging().getChild(__name__)

# ───────────────────────── Constants ────────────────────────────
HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

MIN_BONUS = int(os.getenv("MIN_BONUS", "100"))  # Minimum bonus percentage to alert

# ───────────────────────── Global stores ────────────────────────
STORE = SourceStore()

# ───────────────────────── Redis helpers ─────────────────────────
_SETTINGS = get_settings()
_R: Final = redis.from_url(_SETTINGS.redis_url, decode_responses=True)

KEY_GPT_CHAT = "miles:gpt_mode:{chat_id}"  # per-chat toggle
KEY_GPT_GLOBAL = "miles:gpt_mode:global"  # global toggle (0 / 1)
KEY_MAX_TOKENS = "miles:openai:max_tokens"  # int


def _chat_enabled(chat_id: int) -> bool:
    global_flag = bool(_R.get(KEY_GPT_GLOBAL) == "1")
    local_flag = bool(_R.get(KEY_GPT_CHAT.format(chat_id=chat_id)) == "1")
    return global_flag or local_flag


# ───────────────────────── GPT toggles ──────────────────────────
async def _toggle_chat(chat_id: int, enabled: bool) -> None:
    if enabled:
        _R.set(KEY_GPT_CHAT.format(chat_id=chat_id), "1")
    else:
        _R.delete(KEY_GPT_CHAT.format(chat_id=chat_id))


async def gpt_on(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return
    await _toggle_chat(update.effective_chat.id, True)
    await update.effective_message.reply_text("🤖 GPT chat mode is ON.")


async def gpt_off(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return
    await _toggle_chat(update.effective_chat.id, False)
    await update.effective_message.reply_text("🛑 GPT chat mode is OFF.")


async def gpt_global(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handles /gpt-global-on and /gpt-global-off"""
    if not update.message or not update.message.text or not update.effective_message:
        return
    enable = update.message.text.endswith("on")
    _R.set(KEY_GPT_GLOBAL, "1" if enable else "0")
    state = "ON" if enable else "OFF"
    await update.effective_message.reply_text(f"🌐 GPT GLOBAL mode {state}")


# ───────────────────────── OpenAI settings ──────────────────────
async def set_max_tokens(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
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
async def diag(update: Update, _: ContextTypes.DEFAULT_TYPE) -> None:
    """Ping OpenAI and Redis; return status."""
    if not update.message:
        return
    async with aiohttp.ClientSession() as sess:
        try:
            timeout = aiohttp.ClientTimeout(total=8)
            async with sess.get(
                "https://api.openai.com/v1/models", timeout=timeout
            ) as r:
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
    """Enhanced GPT call with comprehensive system understanding."""
    try:
        import openai
        from config import get_settings

        settings = get_settings()
        if settings.openai_api_key == "not_set":
            return "❌ OpenAI API key not configured"

        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)

        # Enhanced system prompt that teaches the AI about the entire system
        system_prompt = """You are Miles Bot, an advanced Brazilian mileage program monitoring system. Here's your complete knowledge base:

🏗️ ARCHITECTURE:
- You're a Telegram bot built with python-telegram-bot
- Modular plugin system for extensible functionality
- APScheduler for automated scanning on cron schedules
- Redis for fast caching and user preferences
- Entry points for dynamic plugin discovery
- Real-time notifications for transfer bonus promotions

🔌 PLUGIN SYSTEM:
- Protocol-based plugin contracts with type safety
- Each plugin has: name, schedule, categories, scrape() method
- Plugins auto-discovered via importlib.metadata entry points
- Environment control via PLUGINS_ENABLED variable
- Zero downtime loading/unloading with error isolation
- Support for both sync and async plugin methods

📊 DATA FLOW:
1. Plugins scrape sources on their schedules
2. Return Promo objects: {program, bonus_pct, start_dt, end_dt, url, title, source}
3. Deduplication and quality scoring
4. Notifications sent via Telegram for qualifying bonuses
5. Storage in Redis for caching and SQLite for persistence

🎯 CORE FUNCTIONS:
- /ask: Manual scan trigger
- /sources: Source management (add/remove/list)
- /update: AI-powered source discovery
- /chat: Natural language interface (that's you!)
- /help: Comprehensive documentation system
- /config: Current settings and status
- /plugins: Plugin management interface
- /brain: AI autonomous control mode

🧠 YOUR CAPABILITIES:
You can help users with:
- Explaining any feature in detail
- Troubleshooting issues
- Optimizing settings
- Managing sources and plugins
- Understanding scan results
- Configuring AI parameters
- Advanced system administration

🔒 SAFETY & BEST PRACTICES:
- Always explain what actions you're suggesting
- Ask for confirmation before making changes
- Provide clear, helpful explanations
- Use emojis and formatting for clarity
- Stay focused on mileage/points topics
- Respect user privacy and data

🎨 COMMUNICATION STYLE:
- Friendly and helpful
- Use clear, structured responses
- Include relevant emojis
- Format with HTML when appropriate
- Provide examples when explaining features
- Be concise but comprehensive

Remember: You're an expert on Brazilian mileage programs, transfer bonuses, and this bot's technical architecture. Help users get the most value from the system!"""

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )

        return response.choices[0].message.content or "No response generated"

    except Exception as e:
        logger.exception("Enhanced GPT call failed")
        return f"⚠️ AI temporarily unavailable: {str(e)}"


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat or not update.effective_message:
        return
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


# ───────────────────────── Help system ─────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Comprehensive help system explaining the entire Miles bot."""

    # If no specific section requested, show main menu
    args = context.args
    section = args[0] if args else "main"

    if section == "main":
        text = """<b>🚀 Miles Bot - Complete Guide</b>

<b>📖 What is Miles Bot?</b>
Advanced Brazilian mileage program monitor that:
• 🔍 Scans 50+ sources for transfer bonus promotions  
• 🧠 Uses AI to discover new sources automatically
• 🔌 Modular plugin system for extensible functionality
• 📱 Real-time Telegram notifications
• 🤖 ChatGPT integration for natural conversations

<b>📚 Help Sections:</b>
/help ai - 🤖 AI Features & ChatGPT
/help config - 🔧 Configuration & Settings  
/help sources - 📊 Source Management
/help plugins - 🔌 Plugin System
/help brain - ⚡ AI Brain Control
/help advanced - 📈 Advanced Features

<b>⚡ Quick Start:</b>
• /ask - Run immediate scan
• /sources - View monitored sites
• /chat <text> - Talk with AI
• /config - Current settings

<b>🎯 Getting Help:</b>
Just ask me anything! I understand natural language.
Example: "How do I add a new mileage source?"
"""

    elif section == "ai":
        text = """<b>🤖 AI Features Guide</b>

<b>💬 ChatGPT Integration:</b>
• /chat <message> - Start AI conversation
• /end - Clear conversation context
• Send images for AI analysis!

<b>⚙️ AI Configuration:</b>
• /setmodel <model> - Change AI model
  Available: gpt-4o-mini, gpt-4o, gpt-4-turbo
• /settemp <0.0-2.0> - Set creativity level
  0.0 = precise, 2.0 = creative
• /setmaxtokens <100-4096> - Response length

<b>🧠 Smart Features:</b>
• Multimodal: Send images for analysis
• Context memory: Remembers conversation
• Function calling: Can control bot features
• Personal preferences: Settings per user

<b>🔒 AI Safety:</b>
• Conversations timeout after 30 minutes
• No sensitive data stored permanently
• Rate limiting prevents abuse

<i>💡 Pro tip: The AI knows everything about this bot and can help with any feature!</i>
"""

    elif section == "config":
        text = """<b>🔧 Configuration Guide</b>

<b>📊 Current Status:</b>
/config - View all current settings
/diag - System diagnostics

<b>🤖 GPT Controls:</b>
/gpt-on - Enable AI for this chat
/gpt-off - Disable AI for this chat  
/gpt-global-on - Enable AI globally
/gpt-global-off - Disable AI globally

<b>⚙️ Bot Settings:</b>
/setmaxtokens <100-4096> - AI response length
/schedule - View scan schedule
/setscantime <hours> - Set scan times (e.g., 8,20)
/setupdatetime <hour> - Set source update time

<b>🔍 Scanning:</b>
• Automatic scans run on schedule
• Manual scan with /ask
• AI-powered source discovery
• Plugin system for extensibility

<b>📱 Notifications:</b>
• Real-time alerts for new bonuses
• Minimum bonus threshold filtering
• Source attribution and details
"""

    elif section == "sources":
        text = """<b>📊 Source Management Guide</b>

<b>📋 Source Commands:</b>
/sources - List all monitored sources
/addsrc <url> - Add new source manually
/rmsrc <id_or_url> - Remove source
/update - AI discovery of new sources

<b>📥 Bulk Operations:</b>
/import <urls> - Import multiple sources
/export - Export all sources as text

<b>🤖 AI-Powered Discovery:</b>
• Automatically finds relevant sites
• Quality scoring and validation
• Duplicate detection and filtering
• Support for multiple search engines

<b>📈 Source Quality:</b>
• Reliability scoring
• Content freshness analysis  
• Bonus detection accuracy
• Historical performance tracking

<b>🎯 Supported Sites:</b>
• Melhores Destinos
• Passageiro de Primeira  
• Pontos pra Voar
• Mestre das Milhas
• Guia do Milheiro
• And 50+ more sources!
"""

    elif section == "plugins":
        text = """<b>🔌 Plugin System Guide</b>

<b>🏗️ Architecture:</b>
Miles uses a modular plugin system where:
• Each plugin monitors specific sources
• Plugins run on independent schedules
• Zero downtime plugin loading/unloading
• Type-safe contracts with error isolation

<b>🔧 Plugin Management:</b>
/plugins - List all available plugins
/plugins enable <name> - Enable plugin
/plugins disable <name> - Disable plugin
/plugins status - Show plugin health

<b>📦 Built-in Plugins:</b>
• demo-hello - Demo plugin (runs hourly)
• source-discovery - AI-powered source finder
• smiles-monitor - Smiles program tracker
• livelo-scanner - Livelo bonus detector

<b>🛠️ Developer Info:</b>
• Protocol-based plugin contracts
• Entry point discovery mechanism  
• APScheduler integration
• Environment variable controls

<b>🎯 Plugin Benefits:</b>
• Modular and maintainable code
• Independent failure domains
• Easy third-party extensions
• Hot-swappable functionality
"""

    elif section == "brain":
        text = """<b>⚡ AI Brain Control Guide</b>

<b>🧠 What is AI Brain?</b>
Advanced AI system that can autonomously:
• Control all bot functions
• Analyze performance and optimize settings
• Discover and validate new sources
• Make intelligent decisions

<b>🎮 Brain Commands:</b>
/brain analyze - AI analyzes bot performance
/brain discover - Find new mileage sources  
/brain scan - Run and analyze scans
/brain optimize - Optimize bot settings
/brain <question> - Ask AI to control anything

<b>🔒 Safety Features:</b>
• Read-only analysis by default
• Explicit confirmation for changes
• Audit trail of all actions
• User override capabilities

<b>💡 Example Usage:</b>
• "Brain, find sources with 100%+ bonuses"
• "Analyze which sources perform best"  
• "Optimize scan frequency for better results"
• "What's the best time to scan for bonuses?"

<b>🚀 Advanced Features:</b>
• Pattern recognition in bonus timing
• Predictive source quality scoring
• Automated parameter tuning
• Performance trend analysis
"""

    elif section == "advanced":
        text = """<b>📈 Advanced Features Guide</b>

<b>🔄 Scheduling System:</b>
• APScheduler with timezone support
• Cron expressions and aliases
• Plugin-specific schedules
• Hot-reload configuration

<b>💾 Data Management:</b>
• Redis for fast caching
• SQLite for persistence  
• YAML for configuration
• JSON for structured data

<b>🌐 Multi-Engine Search:</b>
• DuckDuckGo integration
• Bing search support
• Content analysis and scoring
• Duplicate detection

<b>📊 Analytics & Monitoring:</b>
• Performance metrics
• Success rate tracking
• Error monitoring and alerts
• Historical trend analysis

<b>🔧 Developer Features:</b>
• Comprehensive test suite
• Type hints and protocols
• Pre-commit hooks
• CI/CD pipeline

<b>🛡️ Security:</b>
• API key encryption
• Rate limiting
• Input validation
• Secure secret management
"""

    else:
        text = f"❌ Unknown help section: {section}\n\nUse /help to see all available sections."

    if update.message:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


# ───────────────────────── Plugin management ────────────────────
async def plugins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Plugin management interface."""
    args = context.args
    action = args[0] if args else "list"

    if action == "list" or action == "status":
        plugins = discover_plugins()
        if not plugins:
            text = "🔌 <b>Plugin System</b>\n\n❌ No plugins currently available.\n\nTo enable plugins, set entry points in pyproject.toml and configure PLUGINS_ENABLED environment variable."
        else:
            lines = ["🔌 <b>Available Plugins</b>\n"]
            for name, plugin in plugins.items():
                status = "✅ Active"
                lines.append(f"<b>{name}</b>")
                lines.append(f"  • Schedule: <code>{plugin.schedule}</code>")
                lines.append(f"  • Categories: {', '.join(plugin.categories)}")
                lines.append(f"  • Status: {status}")
                lines.append("")

            lines.append("📋 <b>Management:</b>")
            lines.append("• <code>/plugins list</code> - Show this list")
            lines.append("• <code>/plugins test &lt;name&gt;</code> - Test plugin")
            lines.append("• <code>/plugins info &lt;name&gt;</code> - Plugin details")

        text = "\n".join(lines)

    elif action == "test" and args and len(args) >= 2:
        plugin_name = args[1]
        plugins = discover_plugins()

        if plugin_name not in plugins:
            text = f"❌ Plugin '{plugin_name}' not found.\n\nUse /plugins list to see available plugins."
        else:
            plugin = plugins[plugin_name]
            try:
                from datetime import datetime

                promos = plugin.scrape(datetime.now())
                text = f"🧪 <b>Testing Plugin: {plugin_name}</b>\n\n✅ Success!\n• Found {len(promos)} promos\n• Schedule: {plugin.schedule}\n• Categories: {', '.join(plugin.categories)}"

                if promos:
                    text += "\n\n📊 <b>Sample Results:</b>"
                    for i, promo in enumerate(promos[:3]):  # Show first 3
                        text += f"\n{i+1}. {promo.get('title', 'Untitled')} ({promo.get('bonus_pct', 0)}%)"

            except Exception as e:
                text = f"❌ <b>Plugin Test Failed: {plugin_name}</b>\n\nError: {str(e)}\n\nCheck plugin implementation and dependencies."

    elif action == "info" and args and len(args) >= 2:
        plugin_name = args[1]
        plugins = discover_plugins()

        if plugin_name not in plugins:
            text = f"❌ Plugin '{plugin_name}' not found."
        else:
            plugin = plugins[plugin_name]
            text = f"""🔌 <b>Plugin Info: {plugin_name}</b>

<b>📋 Details:</b>
• Name: <code>{plugin.name}</code>
• Schedule: <code>{plugin.schedule}</code>
• Categories: {', '.join(plugin.categories)}

<b>🔧 Technical:</b>
• Type: {type(plugin).__name__}
• Module: {type(plugin).__module__}

<b>🧪 Actions:</b>
• Test: <code>/plugins test {plugin_name}</code>
• Manual run: <code>/ask</code> (runs all plugins)"""

    else:
        text = """❌ <b>Invalid plugin command</b>

<b>📋 Available commands:</b>
• <code>/plugins</code> - List all plugins
• <code>/plugins list</code> - Same as above  
• <code>/plugins status</code> - Plugin status
• <code>/plugins test &lt;name&gt;</code> - Test specific plugin
• <code>/plugins info &lt;name&gt;</code> - Plugin information

<b>💡 Examples:</b>
• <code>/plugins test demo-hello</code>
• <code>/plugins info demo-hello</code>"""

    if update.message:
        await update.message.reply_text(
            text, parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


# ───────────────────────── Dynamic /config ──────────────────────
async def config_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.effective_chat:
        return
    chat_id = update.effective_chat.id
    gpt_state = "ON ✅" if _chat_enabled(chat_id) else "OFF ❌"
    max_tok = _R.get(KEY_MAX_TOKENS) or "1000 (default)"
    # ⬇︎ build list from dispatcher so it never goes stale
    app: Any = context.application
    lines: List[str] = [
        "<b>🤖 Current Configuration</b>",
        "",
        "<b>OpenAI</b>",
        f"• GPT per-chat: <b>{gpt_state}</b>",
        f"• Max Tokens: <b>{max_tok}</b>",
        "",
        "<b>Available Commands</b>",
    ]

    # Get commands from handlers instead of app.commands (which doesn't exist)
    handlers = app.handlers.get(0, [])  # Get default group handlers
    for handler in handlers:
        if hasattr(handler, "commands") and handler.commands:
            for cmd in handler.commands:
                if not cmd.startswith("_"):  # skip internal commands
                    lines.append(f"• /{cmd}")

    if update.message:
        await update.message.reply_text(
            "\n".join(lines), parse_mode=ParseMode.HTML, disable_web_page_preview=True
        )


# ───────────────────────── Build application ────────────────────
def build_app() -> Any:
    builder = (
        ApplicationBuilder()
        .token(_SETTINGS.telegram_bot_token)
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
    app.add_handler(CommandHandler(["config"], config_cmd))
    app.add_handler(CommandHandler(["help"], help_cmd))
    app.add_handler(CommandHandler(["plugins"], plugins_cmd))
    app.add_handler(CommandHandler("diag", diag))

    # Catch-all text
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


# ───────────────────────── Utility functions ─────────────────────
def fetch(url: str) -> str | None:
    """Fetch content from a URL"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        return response.text
    except Exception as e:
        print(f"Failed to fetch {url}: {e}")
        return None


# ───────────────────────── Telegram utilities ───────────────────
def send_telegram(message: str, chat_id: str | None = None) -> None:
    """Send telegram message (placeholder implementation)"""
    import os

    token = os.getenv("TELEGRAM_BOT_TOKEN", _SETTINGS.telegram_bot_token)
    if not token or token == "not_set":
        print(f"[TELEGRAM] {message}")
        return

    target_chat = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
    if not target_chat:
        print(f"[TELEGRAM] {message}")
        return

    try:
        import requests

        requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": target_chat, "text": message},
            timeout=10,
        )
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}: {message}")


# ───────────────────────── Scanning functions ────────────────────
def scan_programs(seen: Set[str]) -> List[Tuple[int, str, str]]:
    """Scan programs for bonuses"""
    alerts: List[Tuple[int, str, str]] = []
    sources = STORE.all() if STORE else []

    for source_url in sources:
        try:
            content = fetch(source_url)
            if content:
                parse_feed(source_url, source_url, seen, alerts)
        except Exception as e:
            print(f"Error scanning {source_url}: {e}")

    return alerts


def parse_feed(
    name: str, url: str, seen: Set[str], alerts: List[Tuple[int, str, str]]
) -> None:
    """Parse feed content for bonus alerts"""
    content = fetch(url)
    if not content:
        return

    import re
    from urllib.parse import urlparse

    # Look for bonus percentages in content
    bonus_patterns = [
        r"(\d+)%\s*b[oô]nus",
        r"transferência.*?(\d+)%",
        r"(\d+)%.*?transfer",
    ]

    for pattern in bonus_patterns:
        matches = re.findall(pattern, content.lower())
        for match in matches:
            try:
                bonus = int(match)
                if bonus >= MIN_BONUS:
                    domain = urlparse(url).netloc
                    alert_key = f"{domain}_{bonus}"
                    if alert_key not in seen:
                        seen.add(alert_key)
                        alerts.append((bonus, domain, f"Transferência {bonus}% bônus"))
            except ValueError:
                continue


async def run_scan() -> None:
    """Run the main scanning process"""
    print("Running mileage program scan...")
    seen: Set[str] = set()
    alerts = scan_programs(seen)

    if alerts:
        for bonus, source, details in alerts:
            message = f"🎯 {bonus}% bonus found on {source}: {details}"
            send_telegram(message)
            print(f"Alert: {message}")
    else:
        print("No new bonuses found")


# ───────────────────────── Entrypoint ───────────────────────────
async def main() -> None:
    app = build_app()
    await app.initialize()
    await app.start()
    if app.updater:
        await app.updater.start_polling()
    await asyncio.Event().wait()


if __name__ == "__main__":
    asyncio.run(main())
