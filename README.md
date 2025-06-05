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
   - `MIN_BONUS` (optional) – minimum percentage to notify. Defaults to `100`.
3. Run the bot locally:
   ```bash
   python bonus_alert_bot.py
   ```

The bot can also run via GitHub Actions using the included workflow.

## Feed Sources

The script checks these sources for promotions:
- Passageiro de Primeira
- Smiles (including Gol promotions)
- LATAM Pass
- TudoAzul
- Promoção Aérea
- Pontos pra Voar
- Melhores Destinos (tag "transferencia-bonus")
- Promomilhas

You can modify `PROGRAMS` in `bonus_alert_bot.py` to add or remove feeds.

## Running Tests

Install test dependencies and run `pytest`:

```bash
pip install -r requirements.txt
pip install pytest
pytest
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
