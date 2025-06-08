#!/usr/bin/env bash
# Test script to verify webhook connectivity
# Usage: ./scripts/ping_webhook.sh http://localhost:5051

if [ -z "$1" ]; then
    echo "Usage: $0 <webhook_url>"
    echo "Example: $0 http://localhost:5051"
    exit 1
fi

WEBHOOK_URL="$1"

echo "Testing webhook at: $WEBHOOK_URL"

curl -s -X POST "$WEBHOOK_URL" \
     -H 'Content-Type: application/json' \
     -d '{"run_id":"local-test","step":"ping","log":"Hello from ping test! This is a sample log message to verify webhook connectivity."}' \
     && echo -e "\n✅ Webhook test successful!"

echo "Check received_logs/local-test.ndjson for the logged payload"
