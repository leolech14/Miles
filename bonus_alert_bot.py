#!/usr/bin/env python3
"""Bonus Alert Bot
-----------------
Scans Smiles, LATAM Pass, and TudoAzul landing pages for transfer bonuses of **100% or more**.
Sends a Telegram alert when such a bonus is found.

Usage:
  TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=123 python bonus_alert_bot.py
"""

import os
import re
import json
import requests
import datetime as dt
from bs4 import BeautifulSoup

PROGRAMS = {
    "Smiles": "https://www.smiles.com.br/promocoes/bancos",
    "LATAM":  "https://www.latam.com/latam-pass/pt_br/novidades/promocoes",
    "TudoAzul": "https://tudoazul.voeazul.com.br/portal/pt/ofertas"
}
BONUS_RE = re.compile(r"(1[01]\d|\d{3}|100)\s*%", re.I)  # 100%+
MIN_BONUS = 100
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
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        return resp.text
    except Exception as e:
        print(f"[ERROR] Failed to fetch {url}: {e}")
        return ""

def send_telegram(msg: str):
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        print("[ERROR] TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set.")
        return
    try:
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            data={"chat_id": chat, "text": msg}
        )
        if not resp.ok:
            print(f"[ERROR] Telegram API error: {resp.text}")
    except Exception as e:
        print(f"[ERROR] Exception sending Telegram message: {e}")

def main():
    state = load_state()
    today = dt.date.today().isoformat()
    found = False
    for name, url in PROGRAMS.items():
        html = scrape(url)
        if not html:
            continue
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        m = BONUS_RE.search(text)
        if not m:
            print(f"[INFO] No bonus found for {name}")
            continue
        bonus = int(re.sub(r"[^0-9]", "", m.group()))
        if bonus < MIN_BONUS:
            print(f"[INFO] Bonus {bonus}% for {name} is below threshold.")
            continue
        key = f"{name}_{bonus}"
        if state.get(key) == today:
            print(f"[INFO] Bonus for {name} already notified today.")
            continue
        msg = f"🔥 {name}: bônus {bonus}% ativo! → {url}"
        print(f"[ALERT] {msg}")
        send_telegram(msg)
        state[key] = today
        found = True
    save_state(state)
    if not found:
        print("[INFO] No qualifying bonuses found.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("[FATAL ERROR]", e)
        raise
