#!/bin/bash
# Telegram MCP Authentication for Miles Bot
# Your API Credentials: ✅ Ready

echo "🔐 Authenticating Telegram MCP with your credentials..."
echo "======================================================"

echo ""
echo "📱 AUTHENTICATION COMMAND:"
echo "Replace +YOUR_PHONE with your real phone number (with country code)"
echo ""

echo 'npx -y @chaindead/telegram-mcp auth \'
echo '      --app-id  22444301 \'
echo '      --api-hash dc9ef3af0fd90487e05f1953edc8d496 \'
echo "      --phone    +5554999628402"

echo ""
echo "🇧🇷 Example for Brazil: +5511987654321"
echo "🇺🇸 Example for US: +1234567890"
echo ""

echo "📋 What happens next:"
echo "  1. You'll receive a code in Telegram"
echo "  2. Paste the code when prompted"
echo "  3. Session file will be saved"
echo "  4. You will see a success message"
echo ""

echo "⚠️  Important: Use the SAME phone number associated with your Telegram account!"
echo ""
