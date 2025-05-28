#!/usr/bin/env python3
"""
Bonus Alert Bot · v2.2‑full  (28 May 2025)
==========================================
Alerta automático de **bônus de transferência** de pontos bancários.
Capta tanto HTML quanto RSS ‑ se falhar, tenta proxy.  Envia ping no
Telegram com percentual, nome da fonte e link.

➡  Uso local rápido
    export TELEGRAM_BOT_TOKEN="<token>"
    export TELEGRAM_CHAT_ID="<id>"
    python bonus_alert_bot.py

➡  Dependências (já instaladas no workflow):
    requests beautifulsoup4 feedparser python‑telegram‑bot
"""
from __future__ import annotations
import os, re, sys, time, warnings
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
import feedparser

# =======================  Config  ============================
MIN_BONUS     = int(os.getenv("MIN_BONUS", 100))   # % mínimo
USE_PROXY     = os.getenv("USE_PROXY", "true").lower() == "true"
TIMEOUT       = int(os.getenv("TIMEOUT", 30))      # seg
DEBUG_ALWAYS  = os.getenv("DEBUG_ALWAYS", "false").lower() == "true"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; BonusAlertBot/2.2; +https://github.com/)"
    )
}

# Fontes (edite à vontade) – URLs HTML ou RSS/XML
PROGRAMS: dict[str, List[str]] = {
    "Smiles": [
        "https://www.melhoresdestinos.com.br/tag/smiles/feed",
        "https://feeds.feedburner.com/PromocoesSmiles"      # novo
    ],
    "LATAM Pass": [
        "https://www.melhoresdestinos.com.br/tag/latam-pass/feed",
        "https://feeds.feedburner.com/PromocoesLatamPass"   # novo
    ],
    "TudoAzul": [
        "https://www.melhoresdestinos.com.br/tag/tudoazul/feed",
        "https://feeds.feedburner.com/PromocoesTudoAzul"    # novo
    ],
    "Melhores Destinos – bônus": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed"
    ],
    "Promo Milhas": [
        "https://promomilhas.com.br/feed/"                  # novo
    ],
    "Passageiro de Primeira": [
        "https://passageirodeprimeira.com/feed/"
    ],
}

# Proxies (string.format(u=url)) – usados em cascata se USE_PROXY e fetch direto falhar
PROXY_TPL: List[str] = [
    "https://r.jina.ai/http://{u}",
    "https://api.allorigins.win/raw?url={u}",
]

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")
if not (TOKEN and CHAT):
    print("[FATAL] TELEGRAM_* env vars faltando", file=sys.stderr)
    sys.exit(1)

# =======================  Helpers  ===========================

def fetch_url(url: str) -> tuple[str|None, str]:
    """Tenta baixar o conteúdo da URL. Se falhar, tenta proxies."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text, url
    except Exception as e:
        print(f"[WARN] direto falhou {url[:60]}… → {e}")
        if not USE_PROXY:
            return None, url
    # proxies
    for tpl in PROXY_TPL:
        pu = tpl.format(u=url)
        try:
            r = requests.get(pu, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            print(f"[INFO] via proxy OK → {pu[:60]}…")
            return r.text, pu
        except Exception as e:
            print(f"[WARN] proxy falhou {pu[:60]}… → {e}")
    return None, url


def bonus_in_html(html: str) -> int|None:
    soup = BeautifulSoup(html, "html.parser")
    m = re.search(r"(\d{2,3}) ?%", soup.get_text(" ", strip=True))
    if m:
        return int(m.group(1))
    return None


def bonus_in_rss(url: str) -> Tuple[int|None, str|None]:
    feed = feedparser.parse(url, request_headers=HEADERS)
    for entry in feed.entries:
        m = re.search(r"(\d{2,3}) ?%", entry.title)
        if m and int(m.group(1)) >= MIN_BONUS:
            return int(m.group(1)), entry.link
    return None, None


def send_telegram(text: str):
    resp = requests.post(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data={"chat_id": CHAT, "text": text, "disable_web_page_preview": True},
        timeout=15,
    )
    try:
        resp.raise_for_status()
    except Exception as e:
        print(f"[WARN] Telegram send falhou → {e}")

# ========================  Main  ============================

def run_scan():
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for name, urls in PROGRAMS.items():
        for url in urls:
            pct = None
            link_found = None
            if url.endswith((".rss", ".xml")):
                pct, link_found = bonus_in_rss(url)
            else:
                html, used_url = fetch_url(url)
                if html:
                    pct = bonus_in_html(html)
                    link_found = used_url
            if pct and pct >= MIN_BONUS:
                send_telegram(f"📣 {pct} % · {name}\n{link_found}")
                print(f"[INFO] {name} {pct}% – alerta enviado")
                break  # evita alertar duas vezes a mesma fonte
    if DEBUG_ALWAYS:
        send_telegram("🤖 BonusAlertBot rodou.")
    print("[INFO] Varredura concluída.")


if __name__ == "__main__":
    warnings.filterwarnings("ignore", category=UserWarning)
    start = time.time()
    run_scan()
    print(f"[INFO] Duration {time.time()-start:.1f}s")
