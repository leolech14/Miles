# Miles - Telegram Bonus Alert Bot

This bot checks several mileage blogs for transfer bonus promotions and sends
Telegram notifications when new deals appear.

## Quick start

1. Configure the secrets `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `MIN_BONUS`
   and `FLY_API_TOKEN` in your GitHub repository.

2. Deploy to Fly.io with a single command:

   ```bash
   gh workflow run deploy-fly
   ```

To run everything locally:

```bash
docker compose up
```

Edit `sources.yaml` to change which pages are scanned.

## Development

Run the checks before committing:

```bash
pytest -q
mypy --strict miles/
```
