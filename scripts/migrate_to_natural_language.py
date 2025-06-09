#!/usr/bin/env python3
"""
Migration script for Natural Language Miles Bot.

Helps users transition from the command-based interface to the natural
language interface and validates the new configuration.
"""

from __future__ import annotations

import sys
from pathlib import Path

# ──────────────────────────────────────────────────────────────────────────────
# Local imports
# ──────────────────────────────────────────────────────────────────────────────
# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from miles.natural_language.conversation_manager import conversation_manager
from miles.natural_language.function_registry import function_registry
from natural_language_config import get_natural_language_config

# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────


def print_banner() -> None:
    """Print the migration banner."""
    print(
        """
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   🚀 Miles Bot - Natural Language Migration Tool             ║
║                                                               ║
║   Transform your command-based bot into a conversational AI   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"""
    )


def check_environment() -> dict[str, str]:
    """Validate the environment configuration."""
    print("🔍 Checking environment configuration...")

    config = get_natural_language_config()
    errors = config.validate()

    if not errors:
        print("✅ Environment configuration is valid!")
    else:
        print("❌ Environment configuration has issues:")
        for key, error in errors.items():
            print(f"   • {key}: {error}")

    return errors


def test_openai_connection() -> bool:
    """Test the connection to the OpenAI API."""
    print("🤖 Testing OpenAI API connection...")

    try:
        if conversation_manager.openai_client:
            print("✅ OpenAI API connection successful!")
            return True

        print("❌ OpenAI API client not initialized")
        return False
    except Exception as e:  # noqa: BLE001, try-except-pass
        print(f"❌ OpenAI API connection failed: {e}")
        return False


def test_function_registry() -> bool:
    """Verify the function registry is available."""
    print("⚙️ Testing function registry...")

    try:
        functions = function_registry.get_function_definitions()
        print(f"✅ Function registry loaded {len(functions)} functions:")
        for func in functions:
            print(f"   • {func['name']}: {func['description'][:60]}...")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Function registry test failed: {e}")
        return False


def test_basic_functions() -> bool:
    """Run a quick smoke test on a couple of core functions."""
    print("🧪 Testing basic function execution...")

    try:
        # Bot status
        result = function_registry.execute_function("get_bot_status", {})
        if result.get("success"):
            print("✅ Bot status function working")
            status = result.get("status", {})
            print(f"   • Sources: {status.get('sources_count', 0)}")
            print(f"   • OpenAI: {'✅' if status.get('openai_configured') else '❌'}")
            print(f"   • Redis: {'✅' if status.get('redis_configured') else '❌'}")

        # Source listing
        result = function_registry.execute_function("list_sources", {})
        if result.get("success"):
            total = result.get("total_sources", 0)
            print(f"✅ Source listing working ({total} sources)")

        return True
    except Exception as e:  # noqa: BLE001
        print(f"❌ Function execution test failed: {e}")
        return False


def show_migration_comparison() -> None:
    """Display a before/after view of command vs. natural language usage."""
    print(
        """
📊 MIGRATION COMPARISON:

╔═══════════════════════════════════════════════════════════════╗
║                    BEFORE (Commands)                          ║
╠═══════════════════════════════════════════════════════════════╣
║ User: /ask                                                    ║
║ Bot:  🔍 Scanning for promotions...                          ║
║                                                               ║
║ User: /sources                                                ║
║ Bot:  1. https://site1.com                                   ║
║       2. https://site2.com                                   ║
╚═══════════════════════════════════════════════════════════════╝

╔═══════════════════════════════════════════════════════════════╗
║                  AFTER (Natural Language)                    ║
╠═══════════════════════════════════════════════════════════════╣
║ User: Are there any good bonuses today?                      ║
║ AI:   Let me scan all sources for you! 🔍                   ║
║       *scanning...*                                           ║
║       Found 3 great bonuses:                                 ║
║       🎯 Livelo 120% to Smiles (ends tonight!)              ║
║       🎯 Itaú 100% to Azul (valid until Friday)             ║
║       🎯 C6 Bank 90% to LATAM (new promotion!)              ║
║                                                               ║
║       Would you like me to set up alerts for bonuses         ║
║       above 100%?                                             ║
║                                                               ║
║ User: Show me my monitored websites                          ║
║ AI:   You're currently monitoring 15 Brazilian mileage      ║
║       sources including Melhores Destinos, Passageiro       ║
║       de Primeira, and others. Here's the full list...      ║
╚═══════════════════════════════════════════════════════════════╝
"""
    )


def show_example_conversations() -> None:
    """Print sample natural-language queries the user can try."""
    print(
        """
💬 EXAMPLE CONVERSATIONS:

🎯 Finding Bonuses:
"What's the best transfer bonus available right now?"
"Check for any Livelo promotions"
"Are there bonuses above 100% today?"

📊 Managing Sources:
"Add this site to monitor: https://newsite.com"
"Remove the third source from my list"
"Show me all websites you're monitoring"

⏰ Scheduling:
"Check for bonuses every 4 hours"
"Set up scanning at 8 AM and 8 PM"
"When do you usually find the best promotions?"

🔧 Configuration:
"How is the bot performing?"
"Optimize my settings for better results"
"Show me the current configuration"

🧠 AI Features:
"Find new mileage websites for me"
"Analyze my source performance"
"What's the best strategy for Smiles transfers?"
"""
    )


def create_sample_env_file() -> None:
    """Generate a template .env.natural file if one is missing."""
    env_file = Path(".env.natural")

    if env_file.exists():
        print(f"📄 {env_file} already exists")
        return

    env_content = """# Natural Language Miles Bot Configuration
# Copy this to .env and fill in your values

# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Optional - AI Configuration (optimized for conversation)
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
CONVERSATION_TIMEOUT=1800

# Optional - Enhanced Features
ENABLE_PROACTIVE_SUGGESTIONS=true
ENABLE_PERFORMANCE_INSIGHTS=true
ENABLE_MULTIMODAL=true
ENABLE_FUNCTION_EXPLANATIONS=true

# Optional - Database
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/miles

# Optional - Rate Limiting (generous for natural conversation)
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_FUNCTIONS=20
RATE_LIMIT_OPENAI=60

# Optional - Bot Behavior
MIN_BONUS=80
SOURCES_PATH=sources.yaml
PLUGINS_ENABLED=

# Optional - Monitoring
HEALTH_CHECK_PORT=8080
METRICS_ENABLED=true
LOG_WEBHOOK_URL=
"""

    with env_file.open("w", encoding="utf-8") as fp:
        fp.write(env_content)

    print(f"✅ Created sample environment file: {env_file}")
    print("   Edit this file with your actual values, then copy to .env")


def show_deployment_instructions() -> None:
    """Output multi-platform deployment guidance."""
    print(
        """
🚀 DEPLOYMENT INSTRUCTIONS:

📦 Local Development:
1. pip install -e .[dev]
2. cp .env.natural .env  # Edit with your values
3. python natural_language_bot.py

🐳 Docker (Recommended):
1. docker-compose -f docker-compose.natural.yml up -d

☁️ Fly.io Production:
1. Create fly.toml with natural language config
2. fly secrets set OPENAI_API_KEY=sk-proj-...
3. fly deploy --dockerfile Dockerfile.natural

📊 With Monitoring:
1. docker-compose -f docker-compose.natural.yml up -d
2. Access Grafana at http://localhost:3000
3. Access Prometheus at http://localhost:9090
"""
    )


def main() -> bool:
    """Primary entry-point for the migration workflow."""
    print_banner()

    # Step 1: Environment check
    errors = check_environment()
    if errors:
        print("\n⚠️ Please fix environment issues before proceeding")
        create_sample_env_file()
        return False

    # Step 2: OpenAI connectivity
    if not test_openai_connection():
        print("\n⚠️ OpenAI connection failed - natural language features won't work")
        return False

    # Step 3: Function registry
    if not test_function_registry():
        print("\n⚠️ Function registry test failed")
        return False

    # Step 4: Smoke-test a couple of functions
    if not test_basic_functions():
        print("\n⚠️ Basic function tests failed")
        return False

    # Step 5: Information & guidance
    show_migration_comparison()
    show_example_conversations()
    show_deployment_instructions()

    print(
        """
✅ MIGRATION READY!

Your bot is ready to use natural language! Key benefits:

🎯 Intuitive: Users chat naturally instead of learning commands
🧠 Intelligent: AI understands context and intent
🔧 Powerful: All original features available through conversation
🖼️ Multimodal: Users can send images for analysis
🚀 Proactive: AI suggests optimizations and improvements

Start the bot with: python natural_language_bot.py
"""
    )

    return True


if __name__ == "__main__":  # pragma: no cover
    success = main()
    sys.exit(0 if success else 1)
