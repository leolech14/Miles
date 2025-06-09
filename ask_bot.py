#!/usr/bin/env python3
"""Telegram command bot to trigger manual scans."""
from __future__ import annotations

import os

import asyncio
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from openai import OpenAI
from miles.chat_store import ChatMemory

from miles.scheduler import setup_scheduler, update_schedule, get_current_schedule
from miles.schedule_config import ScheduleConfig
from miles.source_search import update_sources
from miles.ai_source_discovery import ai_update_sources
from miles.source_store import SourceStore

import miles.bonus_alert_bot as bot
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

print("[ask_bot] Starting up...")
print(f"[ask_bot] Python version: {__import__('sys').version}")
print(f"[ask_bot] Working directory: {os.getcwd()}")
print(f"[ask_bot] TELEGRAM_BOT_TOKEN set: {'TELEGRAM_BOT_TOKEN' in os.environ}")
print(f"[ask_bot] REDIS_URL: {os.getenv('REDIS_URL', 'NOT_SET')}")
print(f"[ask_bot] OPENAI_API_KEY set: {'OPENAI_API_KEY' in os.environ}")
print(f"[ask_bot] PORT env var: {os.getenv('PORT', 'NOT_SET')}")

REQUIRED_ENV_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
]

OPTIONAL_ENV_VARS = [
    "OPENAI_API_KEY",  # Only needed for /chat command
    "REDIS_URL",  # Falls back to file storage
    "MIN_BONUS",  # Has default value
]


def check_environment_variables() -> None:
    """Check required environment variables and exit if missing"""
    print(
        f"[ask_bot] Checking required environment variables: {', '.join(REQUIRED_ENV_VARS)}"
    )
    missing = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
    if missing:
        print(
            f"[ask_bot] ERROR: Missing required environment variables: {', '.join(missing)}"
        )
        raise SystemExit(
            f"Missing required environment variables: {', '.join(missing)}"
        )
    print("[ask_bot] All required environment variables are set")

    # STRICT VALIDATION: Check OPENAI_API_KEY is not a zombie value
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key and openai_key in {"not_set", "dummy", "placeholder"}:
        print(f"[ask_bot] 🚫 OPENAI_API_KEY has invalid zombie value: '{openai_key}'")
        print("[ask_bot] To fix:")
        print("[ask_bot]   fly secrets set OPENAI_API_KEY=sk-proj-...")
        print("[ask_bot]   gh secret set OPENAI_API_KEY -b'sk-proj-...'")
        raise SystemExit("OPENAI_API_KEY contains invalid placeholder value")

    # Check optional variables and warn if missing
    print(
        f"[ask_bot] Checking optional environment variables: {', '.join(OPTIONAL_ENV_VARS)}"
    )
    missing_optional = [var for var in OPTIONAL_ENV_VARS if not os.getenv(var)]
    if missing_optional:
        print(
            f"[ask_bot] WARNING: Missing optional environment variables: {', '.join(missing_optional)}"
        )
        print("[ask_bot] Some features may be disabled:")
        for var in missing_optional:
            if var == "OPENAI_API_KEY":
                print("[ask_bot] - /chat command will not work")
            elif var == "REDIS_URL":
                print("[ask_bot] - Using file storage instead of Redis")
            elif var == "MIN_BONUS":
                print("[ask_bot] - Using default minimum bonus threshold")
    else:
        print("[ask_bot] All optional environment variables are set")


# Environment variables will be checked in main


def get_openai_client() -> OpenAI:
    """Get OpenAI client, checking for API key"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or api_key == "not_set":
        raise ValueError(
            "OPENAI_API_KEY is missing or not configured. Please update your environment variables."
        )
    return OpenAI(api_key=api_key)


# Initialize components - OpenAI client will be set in main()
openai_client = None
memory = ChatMemory()
store = SourceStore()


async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Run the scan and reply with any found promotions."""
    if not update.message or not update.effective_chat:
        return
    await update.message.reply_text("🔍 Scanning for promotions ≥80%...")
    seen: set[str] = set()
    alerts = bot.scan_programs(seen)
    if not alerts:
        await update.message.reply_text("✅ Scan complete. No new promotions found.")
        return
    else:
        await update.message.reply_text(
            f"✅ Scan complete. Found {len(alerts)} promotions!"
        )


async def handle_sources(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message:
        return
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
    if not update.message or not update.message.text:
        return
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
    if not update.message or not update.message.text:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /rmsrc <index|url>")
        return
    target = parts[1].strip()
    try:
        # Check if target is an index
        if target.isdigit():
            idx = int(target) - 1
            sources = store.all()
            if 0 <= idx < len(sources):
                target = sources[idx]
            else:
                await update.message.reply_text("Invalid index.")
                return

        removed = store.remove(target)
        if removed:
            await update.message.reply_text(f"🗑️ removed: {removed}")
        else:
            await update.message.reply_text("Not found.")
    except Exception as e:
        await update.message.reply_text(f"Error: {str(e)}")


async def handle_update(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Search for new sources using AI-powered discovery."""
    if not update.message:
        return
    await update.message.reply_text("🧠 AI is searching for new mileage sources...")

    # Try AI-powered discovery first
    try:
        added = ai_update_sources()
        if added:
            msg = f"🧠 AI discovered {len(added)} high-quality sources:\n" + "\n".join(
                added
            )
        else:
            msg = "🧠 AI analysis complete. No new high-quality sources found."
    except Exception:
        # Fallback to basic search
        await update.message.reply_text("⚠️ AI search failed, using basic method...")
        added = update_sources()
        if added:
            msg = "📋 Basic search found new sources:\n" + "\n".join(added)
        else:
            msg = "📋 No new sources found with basic search."

    await update.message.reply_text(msg)


async def handle_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    # Check if OpenAI is available
    if not openai_client:
        if not update.message:
            return
        await update.message.reply_text(
            "❌ Chat feature is not available. OpenAI API key not configured."
        )
        return

    if not update.message or not update.message.text or not update.effective_user:
        return
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /chat <message>")
        return

    user_id = update.effective_user.id
    user_msgs = memory.get(user_id)

    # Add system prompt for bot configuration
    if not user_msgs:
        system_prompt = {
            "role": "system",
            "content": "You are an AI assistant helping to configure a Miles telegram bot that monitors Brazilian mileage program promotions. You can help users configure bot settings, understand commands, and provide general assistance. When users ask about bot configuration, provide helpful guidance.",
        }
        user_msgs.append(system_prompt)

    user_msgs.append({"role": "user", "content": parts[1]})

    try:
        # Get user preferences for model and temperature
        model = memory.get_user_preference(user_id, "model") or os.getenv(
            "OPENAI_MODEL", "gpt-4o-mini"
        )
        temperature = float(memory.get_user_preference(user_id, "temperature") or "0.7")
        max_tokens = int(memory.get_user_preference(user_id, "max_tokens") or "1000")

        resp = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=model,
            messages=user_msgs[-20:],
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not resp.choices or not resp.choices[0].message:
            await update.message.reply_text("❌ Invalid response from OpenAI API.")
            return

        reply = resp.choices[0].message.content
        if not reply:
            await update.message.reply_text("❌ Empty response from OpenAI API.")
            return

    except Exception as e:
        await update.message.reply_text(f"❌ OpenAI API error: {str(e)}")
        return

    user_msgs.append({"role": "assistant", "content": reply})
    memory.save(user_id, user_msgs[-20:])
    await update.message.reply_text(reply)


async def handle_end(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.effective_user:
        return
    memory.clear(update.effective_user.id)
    await update.message.reply_text("\u2702\ufe0f  Chat ended.")


async def handle_config(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current configuration and available options"""
    if not update.message or not update.effective_user:
        return
    user_id = update.effective_user.id
    prefs = memory.get_all_user_preferences(user_id)

    current_model = prefs.get("model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    current_temp = prefs.get("temperature", "0.7")
    current_max_tokens = prefs.get("max_tokens", "1000")

    msg = f"""🤖 **Current Configuration**

**OpenAI Settings:**
• Model: `{current_model}`
• Temperature: `{current_temp}`
• Max Tokens: `{current_max_tokens}`

**Available Commands:**
• `/ask` - Run manual promotion scan
• `/sources` - List current sources  
• `/addsrc <url>` - Add new source URL
• `/rmsrc <id_or_url>` - Remove source by index or URL
• `/update` - AI-powered search for new sources
• `/chat <text>` - Talk with integrated AI assistant
• `/end` - Clear chat context
• `/config` - Show current configuration

**AI Configuration:**
• `/setmodel <model>` - Change AI model
• `/settemp <0.0-2.0>` - Set temperature (0.0-2.0)
• `/setmaxtokens <100-4096>` - Set max response tokens

**Source Management:**  
• `/import <urls>` - Import sources from URLs in text
• `/export` - Export all sources as text

**Scheduling:**
• `/schedule` - View current scan/update schedule
• `/setscantime <hours>` - Set promotion scan times (e.g., 8,20)
• `/setupdatetime <hour>` - Set source update time (e.g., 7)

**Advanced:**
• `/brain <command>` - Let AI control and optimize the bot
• `/debug` - Show bot status and diagnostics

**Available Models:**
• gpt-4o-mini (fastest, cheapest)
• gpt-4o (most capable)
• gpt-4-turbo
• gpt-3.5-turbo"""

    await update.message.reply_text(msg, parse_mode="Markdown")


async def handle_setmodel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the OpenAI model for chat"""
    if not update.message or not update.message.text or not update.effective_user:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: /setmodel <model>\nAvailable: gpt-4o-mini, gpt-4o, gpt-4-turbo, gpt-3.5-turbo"
        )
        return

    model = parts[1].strip()
    valid_models = ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"]

    if model not in valid_models:
        await update.message.reply_text(
            f"Invalid model. Available: {', '.join(valid_models)}"
        )
        return

    user_id = update.effective_user.id
    memory.set_user_preference(user_id, "model", model)
    await update.message.reply_text(f"✅ Model set to: {model}")


async def handle_settemp(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the temperature for AI responses"""
    if not update.message or not update.message.text or not update.effective_user:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /settemp <0.0-2.0>")
        return

    try:
        temp = float(parts[1].strip())
        if not 0.0 <= temp <= 2.0:
            await update.message.reply_text("Temperature must be between 0.0 and 2.0")
            return

        user_id = update.effective_user.id
        memory.set_user_preference(user_id, "temperature", str(temp))
        await update.message.reply_text(f"✅ Temperature set to: {temp}")
    except ValueError:
        await update.message.reply_text(
            "Invalid temperature value. Use a number between 0.0 and 2.0"
        )


async def handle_setmaxtokens(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the max tokens for AI responses"""
    if not update.message or not update.message.text or not update.effective_user:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /setmaxtokens <number>")
        return

    try:
        max_tokens = int(parts[1].strip())
        if not 100 <= max_tokens <= 4096:
            await update.message.reply_text("Max tokens must be between 100 and 4096")
            return

        user_id = update.effective_user.id
        memory.set_user_preference(user_id, "max_tokens", str(max_tokens))
        await update.message.reply_text(f"✅ Max tokens set to: {max_tokens}")
    except ValueError:
        await update.message.reply_text(
            "Invalid number. Use an integer between 100 and 4096"
        )


async def handle_import(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Import sources from a URL or file"""
    if not update.message or not update.message.text:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text("Usage: /import <url_or_text_with_urls>")
        return

    import re

    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    urls = re.findall(url_pattern, parts[1])

    if not urls:
        await update.message.reply_text("No valid URLs found in input")
        return

    added = 0
    for url in urls:
        if store.add(url):
            added += 1

    await update.message.reply_text(
        f"✅ Added {added} new sources from {len(urls)} URLs provided"
    )


async def handle_export(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Export all sources as a text list"""
    if not update.message:
        return
    sources = store.all()
    if not sources:
        await update.message.reply_text("No sources to export")
        return

    text = "\n".join(sources)
    if len(text) > 4000:  # Telegram message limit
        # Split into chunks
        chunks = []
        lines = sources
        current_chunk: list[str] = []
        current_length = 0

        for line in lines:
            if current_length + len(line) + 1 > 4000:
                chunks.append("\n".join(current_chunk))
                current_chunk = [line]
                current_length = len(line)
            else:
                current_chunk.append(line)
                current_length += len(line) + 1

        if current_chunk:
            chunks.append("\n".join(current_chunk))

        for i, chunk in enumerate(chunks):
            await update.message.reply_text(
                f"📋 **Sources Export (Part {i+1}/{len(chunks)})**\n\n{chunk}",
                parse_mode="Markdown",
            )
    else:
        await update.message.reply_text(
            f"📋 **Sources Export ({len(sources)} sources)**\n\n{text}",
            parse_mode="Markdown",
        )


async def handle_schedule(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Show current schedule and allow modifications"""
    if not update.message:
        return
    config = get_current_schedule()

    scan_hours = config.get("scan_hours", [])
    if isinstance(scan_hours, list):
        scan_times = ", ".join(f"{h}:00" for h in scan_hours)
    else:
        scan_times = "Not configured"

    current_schedule = f"""⏰ **Current Schedule** (São Paulo time)

**Source Updates:** {config.get("update_hour", 7)}:00 daily
**Promotion Scans:** {scan_times} daily

To modify schedule times, use:
• `/setscantime <hours>` - Set scan times (e.g., "8,20" for 8AM and 8PM)
• `/setupdatetime <hour>` - Set source update time (e.g., 7 for 7AM)

Note: Times are in 24-hour format, São Paulo timezone"""

    await update.message.reply_text(current_schedule, parse_mode="Markdown")


async def handle_setscantime(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the promotion scan times"""
    if not update.message or not update.message.text:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: /setscantime <hours>\nExample: /setscantime 8,20 (for 8AM and 8PM)"
        )
        return

    try:
        hours_str = parts[1].strip()
        hours = [int(h.strip()) for h in hours_str.split(",")]

        if not all(0 <= h <= 23 for h in hours):
            await update.message.reply_text("All hours must be between 0 and 23")
            return

        if len(hours) > 6:
            await update.message.reply_text("Maximum 6 scan times per day")
            return

        schedule_config = ScheduleConfig()
        if schedule_config.set_scan_times(hours):
            if update_schedule():
                scan_times = ", ".join(f"{h}:00" for h in sorted(hours))
                await update.message.reply_text(
                    f"✅ Promotion scan times set to: {scan_times}"
                )
            else:
                await update.message.reply_text("❌ Failed to update scheduler")
        else:
            await update.message.reply_text("❌ Failed to save schedule configuration")
    except ValueError:
        await update.message.reply_text(
            "Invalid hours format. Use comma-separated numbers (e.g., 8,20)"
        )


async def handle_setupdatetime(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Set the source update time"""
    if not update.message or not update.message.text:
        return
    parts = update.message.text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: /setupdatetime <hour>\nExample: /setupdatetime 7 (for 7AM)"
        )
        return

    try:
        hour = int(parts[1].strip())

        if not 0 <= hour <= 23:
            await update.message.reply_text("Hour must be between 0 and 23")
            return

        schedule_config = ScheduleConfig()
        if schedule_config.set_update_time(hour):
            if update_schedule():
                await update.message.reply_text(
                    f"✅ Source update time set to: {hour}:00"
                )
            else:
                await update.message.reply_text("❌ Failed to update scheduler")
        else:
            await update.message.reply_text("❌ Failed to save schedule configuration")
    except ValueError:
        await update.message.reply_text(
            "Invalid hour format. Use a number between 0 and 23"
        )


async def handle_image_chat(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle image messages for multimodal chat"""
    if not openai_client:
        if not update.message:
            return
        await update.message.reply_text(
            "❌ Chat feature is not available. OpenAI API key not configured."
        )
        return

    if not update.message or not update.message.photo or not update.effective_user:
        return

    user_id = update.effective_user.id
    user_msgs = memory.get(user_id)

    # Add system prompt for bot configuration if first message
    if not user_msgs:
        system_prompt = {
            "role": "system",
            "content": "You are an AI assistant helping to configure a Miles telegram bot that monitors Brazilian mileage program promotions. You can analyze images and help users with visual content. You can help users configure bot settings, understand commands, and provide general assistance.",
        }
        user_msgs.append(system_prompt)

    # Get the largest photo
    photo = update.message.photo[-1]

    try:
        # Download the image
        file = await photo.get_file()
        file_url = file.file_path

        # Prepare message content with image
        content = [{"type": "image_url", "image_url": {"url": file_url}}]

        # Add text caption if provided
        if update.message.caption:
            content.insert(0, {"type": "text", "text": update.message.caption})
        else:
            content.insert(
                0, {"type": "text", "text": "What do you see in this image?"}
            )

        user_msgs.append({"role": "user", "content": content})

        # Get user preferences
        model = (
            memory.get_user_preference(user_id, "model") or "gpt-4o"
        )  # Use gpt-4o for vision
        temperature = float(memory.get_user_preference(user_id, "temperature") or "0.7")
        max_tokens = int(memory.get_user_preference(user_id, "max_tokens") or "1000")

        # Ensure we use a vision-capable model
        if model not in ["gpt-4o", "gpt-4-turbo"]:
            model = "gpt-4o"

        resp = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model=model,
            messages=user_msgs[-10:],  # Keep fewer messages for vision models
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        if not resp.choices or not resp.choices[0].message:
            await update.message.reply_text("❌ Invalid response from OpenAI API.")
            return

        reply = resp.choices[0].message.content
        if not reply:
            await update.message.reply_text("❌ Empty response from OpenAI API.")
            return

    except Exception as e:
        await update.message.reply_text(f"❌ OpenAI API error: {str(e)}")
        return

    user_msgs.append({"role": "assistant", "content": reply})
    memory.save(user_id, user_msgs[-10:])
    await update.message.reply_text(reply)


async def handle_debug(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Debug command to check bot status"""
    if not update.message or not update.effective_user:
        return
    import os

    status_msg = "🔧 **Bot Debug Status**\n\n"

    # OpenAI Status
    if openai_client:
        status_msg += "✅ OpenAI: Connected\n"
    else:
        status_msg += "❌ OpenAI: Not available\n"

    # Environment Variables
    status_msg += (
        f"🔑 OPENAI_API_KEY: {'Set' if os.getenv('OPENAI_API_KEY') else 'Missing'}\n"
    )
    status_msg += f"🤖 TELEGRAM_BOT_TOKEN: {'Set' if os.getenv('TELEGRAM_BOT_TOKEN') else 'Missing'}\n"
    status_msg += f"💬 TELEGRAM_CHAT_ID: {'Set' if os.getenv('TELEGRAM_CHAT_ID') else 'Missing'}\n"
    status_msg += f"📊 REDIS_URL: {'Set' if os.getenv('REDIS_URL') else 'Missing'}\n"

    # Sources Count
    sources_count = len(store.all())
    status_msg += f"🔗 Sources: {sources_count} configured\n"

    # Memory Status
    try:
        user_id = update.effective_user.id
        prefs = memory.get_all_user_preferences(user_id)
        status_msg += f"🧠 Memory: {'Working' if memory else 'Error'}\n"
        status_msg += f"⚙️ User Prefs: {len(prefs)} set\n"
    except Exception as e:
        status_msg += f"🧠 Memory: Error - {e}\n"

    await update.message.reply_text(status_msg, parse_mode="Markdown")


async def handle_ai_brain(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """AI Brain command - let AI control the bot intelligently"""
    if not openai_client:
        if not update.message:
            return
        await update.message.reply_text(
            "❌ AI Brain not available. OpenAI API key not configured."
        )
        return

    if not update.message or not update.message.text or not update.effective_chat:
        return
    
    text = update.message.text
    parts = text.split(maxsplit=1)
    if len(parts) < 2:
        await update.message.reply_text(
            "🧠 AI Brain Commands:\n"
            "• `/brain analyze` - Analyze current bot performance\n"
            "• `/brain optimize` - Optimize source list and settings\n"
            "• `/brain discover` - Discover new sources intelligently\n"
            "• `/brain scan` - Run intelligent promotion scan\n"
            "• `/brain <question>` - Ask AI to control the bot"
        )
        return

    command = parts[1].strip().lower()

    # Add brain system prompt
    brain_messages = [
        {
            "role": "system",
            "content": """You are the AI Brain of the Miles Telegram bot. You can intelligently control the bot's functions:

AVAILABLE ACTIONS:
- analyze_sources: Review current source quality and performance
- discover_sources: Find new high-quality mileage sources
- scan_promotions: Run promotion scan and analyze results
- optimize_settings: Suggest optimal bot configuration
- manage_schedule: Recommend scan timing improvements

You have access to:
- Source list management (add/remove sources)
- Promotion scanning with bonus detection
- User preference management
- Schedule configuration
- Brazilian mileage program expertise

When users ask you to do something, provide a detailed action plan and execute it intelligently. Be proactive and autonomous in managing the bot.""",
        }
    ]

    brain_messages.append({"role": "user", "content": f"Command: {parts[1]}"})

    try:
        await update.message.reply_text("🧠 AI Brain analyzing request...")

        # Get AI response
        response = await asyncio.to_thread(
            openai_client.chat.completions.create,
            model="gpt-4o",  # Use more powerful model for brain functions
            messages=brain_messages,
            temperature=0.3,  # Lower temperature for more focused responses
            max_tokens=1500,
        )

        ai_response = response.choices[0].message.content

        # Execute specific brain commands
        if "analyze" in command:
            await update.message.reply_text("🧠 Analyzing bot performance...")
            sources = store.all()
            analysis = f"""🔍 **Bot Analysis Report**

📊 **Current Status:**
• Sources monitored: {len(sources)}
• OpenAI status: {'✅ Active' if openai_client else '❌ Inactive'}
• Storage: {'Redis + File fallback' if os.getenv('REDIS_URL') else 'File only'}

🎯 **AI Recommendations:**
{ai_response}

💡 Use `/brain optimize` for specific improvements."""
            await update.message.reply_text(analysis, parse_mode="Markdown")

        elif "discover" in command:
            await update.message.reply_text(
                "🧠 AI Brain initiating intelligent source discovery..."
            )
            added = ai_update_sources()
            if added:
                msg = (
                    f"🧠 **Brain Discovery Results:**\n\nFound {len(added)} high-quality sources:\n"
                    + "\n".join(added)
                )
            else:
                msg = "🧠 **Brain Analysis:** Current source list is optimal. No new high-quality sources found."
            await update.message.reply_text(msg, parse_mode="Markdown")

        elif "scan" in command:
            await update.message.reply_text(
                "🧠 AI Brain running intelligent promotion scan..."
            )
            seen: set[str] = set()
            alerts = bot.scan_programs(seen)
            brain_analysis = f"""🧠 **Brain Scan Analysis:**

📈 **Results:** {len(alerts)} promotions found
🎯 **Quality:** {'High-value opportunities detected' if alerts else 'Market currently quiet'}
🔄 **Recommendation:** {ai_response}

{'🚀 Alerts sent!' if alerts else '⏳ Continue monitoring'}"""
            await update.message.reply_text(brain_analysis, parse_mode="Markdown")

        else:
            # General AI brain response
            await update.message.reply_text(
                f"🧠 **AI Brain Response:**\n\n{ai_response}", parse_mode="Markdown"
            )

    except Exception as e:
        await update.message.reply_text(f"🧠❌ Brain error: {str(e)}")


async def _post_init(app: object) -> None:
    try:
        print("[ask_bot] Setting up scheduler...")
        setup_scheduler()
        print("[ask_bot] Scheduler setup complete")
    except Exception as e:
        print(f"[ask_bot] Scheduler setup failed: {e}")
        import traceback

        traceback.print_exc()
        # Don't raise - continue without scheduler


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")


def start_health_server() -> None:
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    threading.Thread(target=server.serve_forever, daemon=True).start()


def main() -> None:
    print("[ask_bot] Starting main function...")

    try:
        print("[ask_bot] Initializing OpenAI client...")
        global openai_client
        try:
            openai_client = get_openai_client()
            print("[ask_bot] ✅ OpenAI client initialized successfully")
            print("[ask_bot] Chat functionality enabled")
        except Exception as e:
            print(f"[ask_bot] ❌ OpenAI client initialization failed: {e}")
            print("[ask_bot] Chat functionality will be disabled")
            print("[ask_bot] Check OPENAI_API_KEY environment variable")
            openai_client = None

        print("[ask_bot] Starting health server...")
        start_health_server()  # Start HTTP health server for Fly.io
        print("[ask_bot] Health server started on port 8080")

        print("[ask_bot] Checking Telegram token...")
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            raise SystemExit("TELEGRAM_BOT_TOKEN is not set")
        print("[ask_bot] Telegram token found")

        print("[ask_bot] Building Telegram application...")
        app = ApplicationBuilder().token(token).post_init(_post_init).build()

        print("[ask_bot] Adding command handlers...")
        app.add_handler(CommandHandler("ask", ask))
        app.add_handler(CommandHandler("sources", handle_sources))
        app.add_handler(CommandHandler("addsrc", handle_addsrc))
        app.add_handler(CommandHandler("rmsrc", handle_rmsrc))
        app.add_handler(CommandHandler("update", handle_update))
        app.add_handler(CommandHandler("chat", handle_chat))
        app.add_handler(CommandHandler("end", handle_end))

        # Configuration commands
        app.add_handler(CommandHandler("config", handle_config))
        app.add_handler(CommandHandler("setmodel", handle_setmodel))
        app.add_handler(CommandHandler("settemp", handle_settemp))
        app.add_handler(CommandHandler("setmaxtokens", handle_setmaxtokens))

        # Enhanced source management
        app.add_handler(CommandHandler("import", handle_import))
        app.add_handler(CommandHandler("export", handle_export))

        # Schedule management
        app.add_handler(CommandHandler("schedule", handle_schedule))
        app.add_handler(CommandHandler("setscantime", handle_setscantime))
        app.add_handler(CommandHandler("setupdatetime", handle_setupdatetime))

        # Image handler for multimodal chat
        app.add_handler(MessageHandler(filters.PHOTO, handle_image_chat))

        # Debug and AI Brain commands
        app.add_handler(CommandHandler("debug", handle_debug))
        app.add_handler(CommandHandler("brain", handle_ai_brain))

        print("[ask_bot] Starting Telegram bot polling...")
        app.run_polling()
    except Exception as e:
        print(f"[ask_bot] Fatal error: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    try:
        check_environment_variables()
        main()
    except KeyboardInterrupt:
        print("[ask_bot] Received keyboard interrupt, shutting down...")
    except SystemExit as e:
        print(f"[ask_bot] System exit: {e}")
        raise
    except Exception as e:
        print(f"[ask_bot] Unexpected error in main: {e}")
        import traceback

        traceback.print_exc()
        raise
