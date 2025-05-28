#!/usr/bin/env python3
"""Bonus Alert Bot
-----------------
Varre landing‑pages de Smiles, LATAM Pass e TudoAzul em busca de
bônus de **100 % ou mais** para transferências de pontos bancários.
Quando encontra, envia alerta via Telegram.

Uso local:
  TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=123 python bonus_alert_bot.py

Automatização: acrescente a workflow do GitHub Actions (exemplo
no README abaixo) e rode de hora em hora.
"""
import os, re, json, requests, datetime as dt
from bs4 import BeautifulSoup

PROGRAMS = {
    "Smiles": "https://www.smiles.com.br/promocoes/pontos-bancos",
    "LATAM": "https://www.latampass.latam.com/pt_br/promocoes/bancos",
    "TudoAzul": "https://tudoazul.voeazul.com.br/promocoes",
}
BONUS_RE = re.compile(r"(1[01]\d|\d{3}|100)\s*%", re.I)  # 100%+
MIN_BONUS = 100  # mude para 120 se quiser só mega promos
STATE_FILE = ".bonus_state.json"


def load_state():
    try:
        with open(STATE_FILE) as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

def scrape(url: str) -> str:
    return requests.get(url, timeout=20).text

def send_telegram(msg: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise SystemExit("⚠ Defina TELEGRAM_BOT_TOKEN e CHAT_ID")
    requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data={"chat_id": chat, "text": msg}
    )


def main():
    state = load_state()
    for name, url in PROGRAMS.items():
        html = scrape(url)
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        m = BONUS_RE.search(text)
        if not m:
            continue
        bonus = int(re.sub(r"[^0-9]", "", m.group()))
        if bonus < MIN_BONUS:
            continue
        key = f"{name}_{bonus}"
        if state.get(key) == dt.date.today().isoformat():
            continue  # já avisado hoje
        send_telegram(f"🔥 {name}: bônus {bonus}% ativo! → {url}")
        state[key] = dt.date.today().isoformat()
    save_state(state)


if __name__ == "__main__":
    main()

"""
# README‑relâmpago

## GitHub Actions
Crie `.github/workflows/bonus.yml`:

```
name: bonus‑alert
on:
  schedule:
    - cron: '0 * * * *'   # a cada hora
  workflow_dispatch:
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.x'}
      - run: pip install requests beautifulsoup4
      - env:
          TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
          TELEGRAM_CHAT_ID:  ${{ secrets.TELEGRAM_CHAT_ID }}
        run: python bonus_alert_bot.py
```

## Segredos
Coloque `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` em *Settings → Secrets & Variables* do repositório.
"""
