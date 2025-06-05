# Miles - Telegram Bonus Alert Bot

This bot monitors airline mileage program blogs and RSS feeds for bonus transfer promotions. When a new promotion meeting the minimum bonus threshold is found, a notification is sent to a Telegram chat.

## Setup

1. Install Python 3.11 and the dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set the following environment variables:
   - `TELEGRAM_BOT_TOKEN` – your Telegram bot token.
   - `TELEGRAM_CHAT_ID` – chat ID that receives the alerts.
   - `MIN_BONUS` (optional) – minimum percentage to notify. Defaults to `80`.
   - `DEBUG_MODE` (optional) – if `True`, always send a test ping.
   - `PROGRAMS_JSON` (optional) – JSON dict with program names and URLs.
3. Run the bot locally:
   ```bash
   python bonus_alert_bot.py
   ```
4. (Optional) Start the command bot that replies to `/ask` on Telegram:
   ```bash
   python ask_bot.py
   ```

The bot can also run via GitHub Actions using the included workflow.

## Feed Sources

The script checks official program pages for promotions. Default sources include:
- Smiles (feed e página de transferências)
- LATAM Pass (feed e página "Bancos Milhas Extras")
- TudoAzul ("Transferir Pontos")
- Livelo (índice de regulamentos ativos)
- Esfera (promoções de viagem)
- Iupp/Itau (pontos e cashback)

You can override the list using the `PROGRAMS_JSON` environment variable.

## Running Tests

Install test dependencies and run `pytest`:

```bash
pip install -r requirements.txt
pip install pytest
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
