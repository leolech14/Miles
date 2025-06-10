#!/bin/bash
# Telegram MCP Setup Script for Miles Bot

echo "🔗 Setting up Telegram MCP Integration..."
echo "=========================================="

echo ""
echo "📋 STEP 1: Get your credentials from https://my.telegram.org"
echo "  1. Login with your phone number"
echo "  2. Go to 'API development tools'"
echo "  3. Create new app: 'Miles MCP Integration'"
echo "  4. Copy the App api_id and App api_hash"
echo ""

echo "📱 STEP 2: Run authentication (replace with your real values):"
echo ""
echo 'npx -y @chaindead/telegram-mcp auth \'
echo '      --app-id  YOUR_APP_ID \'
echo '      --api-hash YOUR_API_HASH \'
echo "      --phone    +YOUR_PHONE_WITH_COUNTRY_CODE"
echo ""

echo "🔧 STEP 3: Add to VS Code settings.json:"
echo ""
echo '{
  "amp.mcpServers": {
    "telegram": {
      "command": "npx",
      "args": ["-y", "@chaindead/telegram-mcp"],
      "env": {
        "TG_APP_ID": "YOUR_APP_ID",
        "TG_API_HASH": "YOUR_API_HASH"
      }
    }
  }
}'
echo ""

echo "🧪 STEP 4: Test in Amp:"
echo "  - Type: list tools"
echo "  - Try: tg_me()"
echo ""

echo "✅ After setup, you'll be able to:"
echo "  - Send messages through MCP"
echo "  - List Telegram dialogs"
echo "  - Monitor chat activity"
echo "  - Debug your Miles bot interactions"
echo ""
