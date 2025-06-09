# Contributing to Miles

## Coding Standards

- Use Black for formatting, Ruff for linting, and mypy for type checking.
- All code must be covered by tests.

## Running Tests

```bash
pytest
```

## Pre-commit

```bash
pre-commit run --all-files
```

## Deployment

- All secrets must be set in GitHub Actions.
- Use `flyctl apps create miles` before first deploy.
```

---

## **5. Add Health Check Endpoint**

If not already present, add a minimal HTTP server for Fly.io health checks.

```python:miles/health.py
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"ok")
        else:
            self.send_response(404)
            self.end_headers()

def run_health_server():
    server = HTTPServer(("0.0.0.0", 8080), HealthHandler)
    server.serve_forever()
```

In your main bot, run this in a background thread.

---

## **6. Enforce Secret Usage and Fail Fast**

At startup, check for all required environment variables and fail with a clear message if any are missing.

```python:miles/bonus_alert_bot.py
import os
import sys

REQUIRED_ENV_VARS = [
    "TELEGRAM_BOT_TOKEN",
    "TELEGRAM_CHAT_ID",
    "MIN_BONUS",
    "SOURCES_PATH",
    "OPENAI_API_KEY"
]

for var in REQUIRED_ENV_VARS:
    if not os.getenv(var):
        print(f"Missing required environment variable: {var}", file=sys.stderr)
        sys.exit(1)
```
