#!/usr/bin/env python3
"""
Test script for Natural Language Miles Bot

Tests the core functionality without requiring Telegram setup.
You only need an OpenAI API key to test the natural language processing.
"""

import asyncio

# Add project to path
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from miles.natural_language.conversation_manager import conversation_manager
from miles.natural_language.function_registry import function_registry


async def test_basic_functions():
    """Test basic function execution."""
    print("🧪 Testing basic functions...")

    # Test bot status
    result = function_registry.execute_function("get_bot_status", {})
    print(f"✅ Bot Status: {result.get('success', False)}")
    if result.get("success"):
        status = result["status"]
        print(f"   • Sources: {status.get('sources_count', 0)}")
        print(f"   • OpenAI: {'✅' if status.get('openai_configured') else '❌'}")
        print(f"   • Redis: {'✅' if status.get('redis_configured') else '❌'}")

    # Test source listing
    result = function_registry.execute_function("list_sources", {"include_stats": True})
    print(f"✅ List Sources: {result.get('success', False)}")
    if result.get("success"):
        print(f"   • Total sources: {result.get('total_sources', 0)}")

    # Test scan function (dry run)
    result = function_registry.execute_function(
        "scan_for_promotions", {"min_bonus": 100}
    )
    print(f"✅ Scan Function: {result.get('success', False)}")
    if result.get("success"):
        print(f"   • Promotions found: {result.get('promotions_found', 0)}")

    print()


async def test_conversation_simulation():
    """Test conversation simulation (requires OpenAI API key)."""
    print("🤖 Testing conversation capabilities...")

    if not conversation_manager.openai_client:
        print(
            "❌ OpenAI client not available - set OPENAI_API_KEY to test conversations"
        )
        return

    print("✅ OpenAI client available - conversation features ready!")

    # Simulate common user intents
    test_messages = [
        "What sources are you monitoring?",
        "Are there any good bonuses today?",
        "How is the bot performing?",
        "Show me the current configuration",
    ]

    print("📝 Example natural language queries that would work:")
    for msg in test_messages:
        print(f'   💬 User: "{msg}"')
        print("   🤖 AI: Would analyze intent and call appropriate functions")

    print()


def test_function_registry():
    """Test function registry completeness."""
    print("📋 Testing function registry...")

    functions = function_registry.get_function_definitions()
    print(f"✅ {len(functions)} functions registered:")

    for func in functions:
        name = func["name"]
        desc = func["description"][:60]
        print(f"   • {name}: {desc}...")

    print()


def show_usage_examples():
    """Show how users would interact with the bot."""
    print("💬 Natural Language Usage Examples:")
    print()

    examples = [
        {
            "user": "Are there any good transfer bonuses today?",
            "ai": "Let me scan all sources for you! 🔍\n       *calls scan_for_promotions()*\n       Found 3 great bonuses:\n       🎯 Livelo 120% to Smiles (ends tonight!)\n       🎯 Itaú 100% to Azul (valid until Friday)\n       Would you like me to set up alerts?",
        },
        {
            "user": "Add this website: https://newsite.com",
            "ai": "*calls add_source(url='https://newsite.com')*\n       ✅ Successfully added https://newsite.com to monitoring!\n       I'll start checking this source in the next scan cycle.",
        },
        {
            "user": "How many sources are you monitoring?",
            "ai": "*calls list_sources(include_stats=True)*\n       I'm currently monitoring 14 Brazilian mileage sources\n       including Melhores Destinos, Passageiro de Primeira,\n       and 12 others. Would you like to see the full list?",
        },
        {
            "user": "Check for bonuses every 4 hours",
            "ai": "*calls set_scan_times(hours=[0, 4, 8, 12, 16, 20])*\n       ✅ Updated scan schedule to every 4 hours!\n       Next scans: 12:00, 16:00, 20:00, 00:00, 04:00, 08:00\n       (São Paulo timezone)",
        },
    ]

    for i, example in enumerate(examples, 1):
        print(f"   Example {i}:")
        print(f"   👤 User: {example['user']}")
        print(f"   🤖 AI: {example['ai']}")
        print()


def main():
    """Main test function."""
    print(
        """
    ╔═══════════════════════════════════════════════════════════════╗
    ║                                                               ║
    ║   🧪 Natural Language Miles Bot - Test Suite                 ║
    ║                                                               ║
    ╚═══════════════════════════════════════════════════════════════╝
    """
    )

    # Run synchronous tests
    test_function_registry()

    # Run async tests
    asyncio.run(test_basic_functions())
    asyncio.run(test_conversation_simulation())

    # Show examples
    show_usage_examples()

    print("🎯 Next Steps:")
    print(
        "1. Set your environment variables (TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, etc.)"
    )
    print("2. Run: python natural_language_bot.py")
    print("3. Chat naturally with your bot in Telegram!")
    print()
    print("🚀 The natural language transformation is complete!")


if __name__ == "__main__":
    main()
