#!/usr/bin/env python3
"""Bonus Alert Bot
===================

Monitor official mileage program pages for point transfer bonuses and alert a
Telegram chat when a new promotion is detected.
"""
from __future__ import annotations

import os
import re
import time
import warnings
import hashlib
import yaml
from urllib.parse import urlparse, urljoin

import feedparser
import requests
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning, Tag
from miles.storage import get_store

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ------------- CONFIGURAÇÃO PRINCIPAL -----------------
MIN_BONUS = int(os.getenv("MIN_BONUS", 80))
DEBUG_ALWAYS = os.getenv("DEBUG_MODE", "False") == "True"
TIMEOUT = 25

SOURCES_PATH = os.getenv("SOURCES_PATH", "sources.yaml")
try:
    with open(SOURCES_PATH) as f:
        SOURCES: list[str] = yaml.safe_load(f)
except FileNotFoundError:
    SOURCES = []


HEADERS = {"User-Agent": "Mozilla/5.0 (BonusAlertBot)"}
PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
    "https://r.jina.ai/http://{u}",
]

BONUS_PCT_RE = re.compile(r"(?P<pct>\d{2,3})\s*%.*?(b[oô]nus|bonus)", re.I)
DOBRO_RE = re.compile(r"\b(dobro|duplicar|2x)\b", re.I)

# Regex helpers for optional extraction
PCT_RE = re.compile(r"(\d{2,3})%")
URL_RE = re.compile(r"https?://\S+")


def extract_pct(text: str) -> str | None:
    m = PCT_RE.search(text)
    return m.group(1) if m else None


def extract_url(text: str) -> str | None:
    m = URL_RE.search(text)
    return m.group(0) if m else None


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


def parse_feed(
    name: str, url: str, seen: set[str], alerts: list[tuple[int, str, str]]
) -> None:
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

        for itm in soup.find_all(["item", "article", "entry", "h2", "h3"]):
            item = itm if isinstance(itm, Tag) else Tag(name="")
            text = item.get_text(" ")[:400]
            a_tag = item.find("a")
            if isinstance(a_tag, Tag):
                href = a_tag.get("href")
                if isinstance(href, str):
                    link = urljoin(url, href)
                else:
                    link = url
            else:
                link = url
            handle_text(name, text, link, seen, alerts)


def handle_text(
    src: str, text: str, link: str, seen: set[str], alerts: list[tuple[int, str, str]]
) -> None:
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


def send_telegram(msg: str, chat_id: str | None = None) -> None:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat = chat_id or os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat:
        raise RuntimeError("Telegram credentials are missing")
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


def scan_programs(seen: set[str]) -> list[tuple[int, str, str]]:
    """Check all program sources and return found alerts."""
    alerts: list[tuple[int, str, str]] = []
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for url in SOURCES:
        name = urlparse(url).netloc
        parse_feed(name, url, seen, alerts)
    if DEBUG_ALWAYS and not alerts:
        alerts.append((0, "Debug", "https://example.com"))
    return alerts


def run_scan(chat_id: str | None = None) -> list[tuple[int, str, str]]:
    """Run a scan and send Telegram messages for new promos."""
    store = get_store()
    seen: set[str] = set()
    alerts = scan_programs(seen)
    for pct, src, link in alerts:
        h = hashlib.sha1(f"{pct}{link}".encode()).hexdigest()
        if store.has(h):
            continue
        line = f"\U0001f4e3 {pct}% \xb7 {src}\n{link}"
        try:
            send_telegram(line, chat_id)
        except Exception as e:
            print("[ERROR] Telegram", e)
        store.add(h)
    return alerts


def main() -> None:
    start = time.time()
    alerts = run_scan()
    print(f"[INFO] Duration {round(time.time()-start,1)}s | alerts: {len(alerts)}")


if __name__ == "__main__":
    main()
