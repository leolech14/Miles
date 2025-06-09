#!/usr/bin/env bash
# Unified secret management for Miles bot
# Sets secrets in both GitHub and Fly.io simultaneously to prevent naming drift

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# List of required and optional secrets
declare -A SECRETS_DESC=(
	[OPENAI_API_KEY]="OpenAI API key (required)"
	[TELEGRAM_BOT_TOKEN]="Telegram bot token (required)"
	[TELEGRAM_CHAT_ID]="Telegram chat ID (required)"
	[MIN_BONUS]="Minimum bonus (optional, default: 80)"
	[REDIS_URL]="Redis URL (optional, leave empty for file fallback)"
)
REQUIRED_SECRETS=(OPENAI_API_KEY TELEGRAM_BOT_TOKEN TELEGRAM_CHAT_ID)
OPTIONAL_SECRETS=(MIN_BONUS REDIS_URL)

# Holds secret values
declare -A SECRET_VALUES

print_usage() {
	echo "Usage: $0 [command] [--SECRET=value ...]"
	echo ""
	echo "Commands:"
	echo "  set-openai     Set OPENAI_API_KEY in both GitHub and Fly"
	echo "  set-telegram   Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID"
	echo "  set-all        Set all required and optional secrets"
	echo "  check          Check secret status in both systems"
	echo ""
	echo "Flags / Env-vars for non-interactive (CI) mode:"
	echo "  --SECRET=value   Provide a secret value via flag (e.g. --OPENAI_API_KEY=sk-...)"
	echo "  Or set environment variables (e.g. export OPENAI_API_KEY=sk-...)"
	echo ""
	echo "Examples:"
	echo "  $0 set-openai --OPENAI_API_KEY=sk-proj-xxxx"
	echo "  $0 set-all"
	echo "  $0 set-all --TELEGRAM_BOT_TOKEN=xxx --TELEGRAM_CHAT_ID=yyy"
	echo "  $0 check"
}

check_dependencies() {
	command -v gh >/dev/null 2>&1 || {
		echo -e "${RED}Error: gh CLI not found${NC}"
		exit 1
	}
	command -v fly >/dev/null 2>&1 || {
		echo -e "${RED}Error: fly CLI not found${NC}"
		exit 1
	}

	if ! gh auth status -h github.com >/dev/null 2>&1; then
		echo -e "${RED}Error: Not authenticated to GitHub CLI. Run 'gh auth login'.${NC}"
		exit 1
	fi
	if ! fly auth whoami >/dev/null 2>&1; then
		echo -e "${RED}Error: Not authenticated to Fly.io CLI. Run 'fly auth login'.${NC}"
		exit 1
	fi
}

# Parse --KEY=VALUE flags into SECRET_VALUES
parse_flags() {
	for arg in "$@"; do
		if [[ ${arg} == --*=* ]]; then
			key="${arg%%=*}"
			key="${key#--}"
			value="${arg#*=}"
			SECRET_VALUES["${key}"]="${value}"
		fi
	done
}

# Get secret value: flag > env > prompt
get_secret() {
	local name="$1"
	local desc="${SECRETS_DESC[${name}]}"
	local silent="${2:-false}"
	local default="${3-}"

	# 1. Flag
	if [[ -n ${SECRET_VALUES[${name}]-} ]]; then
		echo "${SECRET_VALUES[${name}]}"
		return
	fi
	# 2. Env
	if [[ -n ${!name-} ]]; then
		echo "${!name}"
		return
	fi
	# 3. Prompt
	if [[ ${silent} == "true" ]]; then
		echo -e "${YELLOW}Enter ${desc}:${NC}"
		read -rs val
		echo
	else
		if [[ -n ${default} ]]; then
			echo -e "${YELLOW}Enter ${desc} [default: ${default}]:${NC}"
			read -r val
			val="${val:-${default}}"
		else
			echo -e "${YELLOW}Enter ${desc}:${NC}"
			read -r val
		fi
	fi
	echo "${val}"
}

set_openai_key() {
	local key
	key="$(get_secret OPENAI_API_KEY true)"
	if [[ ! ${key} =~ ^sk-proj- ]]; then
		echo -e "${RED}Warning: Key doesn't start with 'sk-proj-', are you sure it's correct? (y/N)${NC}"
		read -r -n 1
		echo
		if [[ ! ${REPLY} =~ ^[Yy]$ ]]; then
			echo "Aborted."
			exit 1
		fi
	fi
	echo "Setting in GitHub..."
	gh secret set OPENAI_API_KEY -b"${key}"
	echo "Setting in Fly.io..."
	fly secrets set OPENAI_API_KEY="${key}"
	echo -e "${GREEN}✅ OPENAI_API_KEY set in both GitHub and Fly.io${NC}"
}

set_telegram_secrets() {
	local bot_token chat_id
	bot_token="$(get_secret TELEGRAM_BOT_TOKEN true)"
	chat_id="$(get_secret TELEGRAM_CHAT_ID false)"
	echo "Setting in GitHub..."
	gh secret set TELEGRAM_BOT_TOKEN -b"${bot_token}"
	gh secret set TELEGRAM_CHAT_ID -b"${chat_id}"
	echo "Setting in Fly.io..."
	fly secrets set TELEGRAM_BOT_TOKEN="${bot_token}" TELEGRAM_CHAT_ID="${chat_id}"
	echo -e "${GREEN}✅ Telegram secrets set in both GitHub and Fly.io${NC}"
}

set_all_secrets() {
	echo -e "${YELLOW}Setting up all required secrets...${NC}"
	# Required
	for name in "${REQUIRED_SECRETS[@]}"; do
		local silent="false"
		[[ ${name} == "OPENAI_API_KEY" || ${name} == "TELEGRAM_BOT_TOKEN" ]] && silent="true"
		SECRET_VALUES["${name}"]="$(get_secret "${name}" "${silent}")"
	done

	# Optional
	SECRET_VALUES["MIN_BONUS"]="$(get_secret MIN_BONUS false 80)"
	SECRET_VALUES["REDIS_URL"]="$(get_secret REDIS_URL false)"

	# Set in GitHub
	for name in "${!SECRET_VALUES[@]}"; do
		val="${SECRET_VALUES[${name}]}"
		if [[ -n ${val} ]]; then
			gh secret set "${name}" -b"${val}"
		fi
	done

	# Set in Fly.io (build up args)
	fly_args=()
	for name in "${!SECRET_VALUES[@]}"; do
		val="${SECRET_VALUES[${name}]}"
		if [[ -n ${val} ]]; then
			fly_args+=("${name}=${val}")
		fi
	done
	if [[ ${#fly_args[@]} -gt 0 ]]; then
		fly secrets set "${fly_args[@]}"
	fi

	echo -e "${GREEN}✅ All secrets configured!${NC}"
}

check_secrets() {
	echo -e "${YELLOW}Checking secret status...${NC}"
	echo ""
	echo "GitHub Secrets:"
	gh secret list | grep -E "(OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID|MIN_BONUS|REDIS_URL)" || echo "No relevant secrets found"
	echo ""
	echo "Fly.io Secrets:"
	fly secrets list | grep -E "(OPENAI_API_KEY|TELEGRAM_BOT_TOKEN|TELEGRAM_CHAT_ID|MIN_BONUS|REDIS_URL)" || echo "No relevant secrets found"
	echo ""
	echo -e "${YELLOW}Next steps:${NC}"
	echo "1. Deploy: gh workflow run deploy-fly"
	echo "2. Test: fly logs --app miles"
	echo "3. Verify: Send /chat ping to your bot"
}

main() {
	check_dependencies
	parse_flags "$@"

	case "${1-}" in
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
