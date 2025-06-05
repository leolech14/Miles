#!/usr/bin/env python3
"""Bonus Alert Bot
===================

Monitor official mileage program pages for point transfer bonuses and alert a
Telegram chat when a new promotion is detected.
"""
from __future__ import annotations

import json
import os
import re
import time
import warnings
from typing import Any

import feedparser
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ------------- CONFIGURAÇÃO PRINCIPAL -----------------
MIN_BONUS = int(os.getenv("MIN_BONUS", 80))
DEBUG_ALWAYS = os.getenv("DEBUG_MODE", "False") == "True"
TIMEOUT = 25

DEFAULT_PROGRAMS: dict[str, list[str]] = {
    "Smiles": [
        "https://www.smiles.com.br/feed",
        "https://www.smiles.com.br/portal/tudo-pra-viajar/bancos-26-05-2025",
    ],
    "LATAM Pass": [
        "https://www.latam.com/latam-pass/feed",
        "https://latampass.latam.com/pt_br/promocao/bancos-pontos-extras",
    ],
    "TudoAzul": [
        "https://www.voeazul.com.br/br/pt/programa-fidelidade/transferir-pontos"
    ],
    "Livelo": ["https://www.livelo.com.br/regulamentos-ativos"],
    "Esfera": [
        "https://latampass.latam.com/pt_br/promocao/esfera-milhas-extras"
    ],
    "Iupp": ["https://www.itau.com.br/pontos-e-cashback"],
}

PROGRAMS: dict[str, list[str]]
try:
    PROGRAMS = json.loads(os.getenv("PROGRAMS_JSON", ""))
    if not isinstance(PROGRAMS, dict):
        raise ValueError
except Exception:
    PROGRAMS = DEFAULT_PROGRAMS


HEADERS = {"User-Agent": "Mozilla/5.0 (BonusAlertBot)"}
PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
    "https://r.jina.ai/http://{u}",
]

BONUS_PCT_RE = re.compile(r"(?P<pct>\d{2,3})\s*%.*?(b[oô]nus|bonus)", re.I)
DOBRO_RE = re.compile(r"\b(dobro|duplicar|2x)\b", re.I)

# ----------------- UTIL ----------------------------


def fetch(url: str) -> str | None:
    try:
        return requests.get(url, headers=HEADERS, timeout=TIMEOUT).text
    except Exception:
        for tpl in PROXY_TPL:
            prox = tpl.format(u=url)
            try:
                return requests.get(prox, headers=HEADERS, timeout=TIMEOUT).text
            except Exception:
                continue
    return None


def parse_feed(name: str, url: str, seen: set[str], alerts: list[tuple[int, str, str]]):
    raw = fetch(url)
    if not raw:
        return
    if url.endswith((".rss", ".xml")) or raw.strip().startswith("<?xml"):
        feed = feedparser.parse(raw)
        entries = feed.entries
        for e in entries:
            text = (e.title + " " + e.get("summary", ""))[:400]
            link = e.link
            handle_text(name, text, link, seen, alerts)
    else:
        soup = BeautifulSoup(raw, "html.parser")
        for item in soup.find_all(["item", "article", "entry", "h2", "h3"]):
            text = item.get_text(" ")[:400]
            link = getattr(item.find("a"), "href", url)
            handle_text(name, text, link, seen, alerts)


def handle_text(
    src: str, text: str, link: str, seen: set[str], alerts: list[tuple[int, str, str]]
):
    text_norm = " ".join(text.split())
    pct_match = BONUS_PCT_RE.search(text_norm)
    pct: int | None = int(pct_match.group("pct")) if pct_match else None
    has_transfer = re.search(r"transf", text_norm, re.I) is not None

    if pct is not None and not has_transfer:
        pct = None

    if pct is None and DOBRO_RE.search(text_norm) and has_transfer:
        pct = 100

    if pct is None:
        return
    if pct < MIN_BONUS and not DEBUG_ALWAYS:
        return
    sig = f"{pct}|{link.split('?')[0]}"
    if sig in seen:
        return
    alerts.append((pct, src, link))
    seen.add(sig)


# ----------------- TELEGRAM ------------------------


def send_telegram(msg: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(
        url,
        data={
            "chat_id": chat,
            "text": msg,
            "disable_web_page_preview": True,
        },
        timeout=15,
    )
    print("[TG]", r.status_code, r.text[:120])
    r.raise_for_status()


# ----------------- MAIN ----------------------------


def main():
    start = time.time()
    seen = load_seen()
    alerts: list[tuple[int, str, str]] = []

    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for src, urls in PROGRAMS.items():
        for url in urls:
            parse_feed(src, url, seen, alerts)

    if DEBUG_ALWAYS and not alerts:
        alerts.append((0, "Debug", "https://example.com"))

    for pct, src, link in alerts:
        msg = f"📣 {pct}% · {src}\n{link}"
        try:
            send_telegram(msg)
        except Exception as e:
            print("[ERROR] Telegram", e)

    save_seen(seen)
    print(f"[INFO] Duration {round(time.time()-start,1)}s | alerts: {len(alerts)}")


# ---------------- PERSISTÊNCIA ---------------------

SEEN_PATH = "seen.json"


def load_seen() -> set[str]:
    if os.path.exists(SEEN_PATH):
        try:
            return set(json.load(open(SEEN_PATH)))
        except Exception:
            return set()
    return set()


def save_seen(seen: set[str]):
    try:
        json.dump(list(seen), open(SEEN_PATH, "w"))
    except Exception:
        pass


if __name__ == "__main__":
    main()
