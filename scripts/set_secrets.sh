#!/usr/bin/env bash
# Unified secret management for Miles bot
# Sets secrets in both GitHub and Fly.io simultaneously to prevent naming drift

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  set-openai     Set OPENAI_API_KEY in both GitHub and Fly"
    echo "  set-telegram   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
    echo "  set-all        Set all required secrets interactively"
    echo "  check          Check secret status in both systems"
    echo ""
    echo "Examples:"
    echo "  $0 set-openai"
    echo "  $0 check"
}

check_dependencies() {
    command -v gh >/dev/null 2>&1 || { echo -e "${RED}Error: gh CLI not found${NC}"; exit 1; }
    command -v fly >/dev/null 2>&1 || { echo -e "${RED}Error: fly CLI not found${NC}"; exit 1; }
}

set_openai_key() {
    echo -e "${YELLOW}Setting OpenAI API Key...${NC}"
    echo "Paste your OpenAI API key (it will be hidden):"
    read -s KEY

    if [[ ! "$KEY" =~ ^sk-proj- ]]; then
        echo -e "${RED}Warning: Key doesn't start with 'sk-proj-', are you sure it's correct? (y/N)${NC}"
        read -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            echo "Aborted."
            exit 1
        fi
    fi

    echo "Setting in GitHub..."
    gh secret set OPENAI_API_KEY -b"$KEY"

    echo "Setting in Fly.io..."
    fly secrets set OPENAI_API_KEY="$KEY"

    echo -e "${GREEN}✅ OPENAI_API_KEY set in both GitHub and Fly.io${NC}"
}

set_telegram_secrets() {
    echo -e "${YELLOW}Setting Telegram secrets...${NC}"

    echo "Enter TELEGRAM_BOT_TOKEN:"
    read -s BOT_TOKEN

    echo "Enter TELEGRAM_CHAT_ID:"
    read CHAT_ID

    echo "Setting in GitHub..."
    gh secret set TELEGRAM_BOT_TOKEN -b"$BOT_TOKEN"
    gh secret set TELEGRAM_CHAT_ID -b"$CHAT_ID"

    echo "Setting in Fly.io..."
    fly secrets set TELEGRAM_BOT_TOKEN="$BOT_TOKEN" TELEGRAM_CHAT_ID="$CHAT_ID"

    echo -e "${GREEN}✅ Telegram secrets set in both GitHub and Fly.io${NC}"
}

set_all_secrets() {
    echo -e "${YELLOW}Setting up all required secrets...${NC}"
    set_openai_key
    echo ""
    set_telegram_secrets

    echo ""
    echo -e "${YELLOW}Setting optional secrets...${NC}"
    echo "Enter MIN_BONUS (default: 80):"
    read MIN_BONUS
    MIN_BONUS=${MIN_BONUS:-80}

    echo "Enter REDIS_URL (leave empty for file fallback):"
    read REDIS_URL
    REDIS_URL=${REDIS_URL:-not_set}

    gh secret set MIN_BONUS -b"$MIN_BONUS"
    gh secret set REDIS_URL -b"$REDIS_URL"

    fly secrets set MIN_BONUS="$MIN_BONUS" REDIS_URL="$REDIS_URL"

    echo -e "${GREEN}✅ All secrets configured!${NC}"
}

check_secrets() {
    echo -e "${YELLOW}Checking secret status...${NC}"
    echo ""

    echo "GitHub Secrets:"
    gh secret list | grep -E "(OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)" || echo "No relevant secrets found"

    echo ""
    echo "Fly.io Secrets:"
    fly secrets list | grep -E "(OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID)" || echo "No relevant secrets found"

    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "1. Deploy: gh workflow run deploy-fly"
    echo "2. Test: fly logs --app miles"
    echo "3. Verify: Send /chat ping to your bot"
}

main() {
    check_dependencies

    case "${1:-}" in
        "set-openai")
            set_openai_key
            ;;
        "set-telegram")
            set_telegram_secrets
            ;;
        "set-all")
            set_all_secrets
            ;;
        "check")
            check_secrets
            ;;
        *)
            print_usage
            exit 1
            ;;
    esac
}

main "$@"
