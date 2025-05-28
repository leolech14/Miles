#!/usr/bin/env python3
"""
Bonus Alert Bot • v2.3  (28 May 2025)
======================================
Monitora promoções de **bônus de transferência de pontos** (Livelo, Esfera, Iupp → Smiles, LATAM Pass, TudoAzul, etc.)
e envia alertas via Telegram.

Principais recursos
-------------------
• Fontes RSS confiáveis + fallback proxy (AllOrigins) se o fetch direto falhar.
• Procura por padrões “NN %” no **título + summary** do feed.
• Envia alerta formatado:  ➜ "📣 120 % • Smiles \n <link>".
• Evita duplicados (hash por URL+percentual).
• DEBUG_ALWAYS força um alerta por execução para teste.

Como executar
-------------
$ export TELEGRAM_BOT_TOKEN="…"
$ export TELEGRAM_CHAT_ID="…"
$ python bonus_alert_bot.py

Dependências: requests, feedparser.
No GitHub Actions:
  - run: pip install requests feedparser

"""
from __future__ import annotations
import os, re, time, hashlib, json, requests, feedparser, textwrap
from typing import List, Tuple, Set

# ========= Config =========
MIN_BONUS   = int(os.getenv("MIN_BONUS", 0))      # % mínimo p/ alertar
DEBUG_ALWAYS= os.getenv("DEBUG_ALWAYS", "True") == "True"
USE_PROXY   = os.getenv("USE_PROXY", "True") == "True"
HEADERS     = {"User-Agent": "Mozilla/5.0 BonusBot"}
TIMEOUT     = 20

PROGRAMS: dict[str, List[str]] = {
    "Smiles": [
        "https://www.melhoresdestinos.com.br/tag/smiles/feed",
        "https://feeds.feedburner.com/promocoes-smiles",
    ],
    "LATAM Pass": [
        "https://www.melhoresdestinos.com.br/tag/latam-pass/feed",
        "https://feeds.feedburner.com/promocoes-latampass",
    ],
    "TudoAzul": [
        "https://www.melhoresdestinos.com.br/tag/tudoazul/feed",
        "https://feeds.feedburner.com/promocoes-tudoazul",
    ],
    "Blog – MD Transferência": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed",
    ],
    "Blog – Passageiro de Primeira": [
        "https://passageirodeprimeira.com/feed/",
    ],
}
PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
]

# ========= Core =========

def log(msg: str):
    print(msg, flush=True)

def fetch_url(url: str) -> str | None:
    """Tenta baixar URL direto; se falhar e USE_PROXY, tenta via proxy."""
    # direto
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        log(f"[WARN] direto falhou {url} → {e}")
    # proxy
    if USE_PROXY:
        for tpl in PROXY_TPL:
            py_url = tpl.format(u=url)
            try:
                r = requests.get(py_url, headers=HEADERS, timeout=TIMEOUT)
                r.raise_for_status()
                log(f"[INFO] via proxy OK → {py_url[:60]}…")
                return r.text
            except Exception as e:
                log(f"[WARN] proxy falhou {py_url[:60]}… → {e}")
    return None

def parse_feed(source: str, html: str) -> List[Tuple[int, str]]:
    """Retorna lista de (percentual, link)."""
    out: List[Tuple[int,str]] = []
    feed = feedparser.parse(html)
    for entry in feed.entries:
        txt = (entry.title + " " + entry.get("summary", ""))[:400]
        m = re.search(r"(\d{2,3})\s?%", txt)
        if m:
            pct = int(m.group(1))
            if pct >= MIN_BONUS:
                out.append((pct, entry.link))
    return out

def send_telegram(msg: str):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat  = os.environ["TELEGRAM_CHAT_ID"]
    url   = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={"chat_id": chat, "text": msg, "disable_web_page_preview": True}, timeout=15)
    log(f"[TG] {r.status_code} {r.text[:80]}")
    if not r.ok:
        r.raise_for_status()

# ========= Runner =========
log(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")

duplicates: Set[str] = set()
start = time.time()

def hash_key(source: str, pct: int, link: str) -> str:
    return hashlib.md5(f"{source}|{pct}|{link}".encode()).hexdigest()

for src, urls in PROGRAMS.items():
    for u in urls:
        html = fetch_url(u)
        if not html:
            continue
        for pct, link in parse_feed(src, html):
            h = hash_key(src, pct, link)
            if h in duplicates:
                continue
            duplicates.add(h)
            if pct >= MIN_BONUS or DEBUG_ALWAYS:
                send_telegram(f"📣 {pct}% · {src}\n{link}")

log(f"[INFO] Duration {round(time.time()-start,1)}s")
