#!/usr/bin/env python3
"""
Bonus Alert Bot · v2.4  (28 May 2025)
======================================
Varre feeds RSS e páginas proxy‑cache de blogs/programas de milhas para achar
promoções de **bônus de transferência** de pontos e avisa via Telegram.

Principais mudanças v2.4
------------------------
• Regex inteligente exige "% + bônus + transfer" (menos ruído).
• `MIN_BONUS` default 80 % (pode alterar via env).
• `DEBUG_ALWAYS` desligado por padrão – definir DEBUG_ALWAYS=1 p/ testes.
• Cache `seen.json` evita alertas duplicados entre execuções.
• Mensagem condensada: "📣 120% · Smiles → link".

Uso local
---------
TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID devem estar em variáveis de ambiente.
Opcional:
  MIN_BONUS      (int, default 80)
  DEBUG_ALWAYS   ("1"/"true" para sempre avisar)

Dependências: requests, feedparser, beautifulsoup4.
"""
from __future__ import annotations
import os, re, json, time, datetime as dt, hashlib, warnings
import requests, feedparser
from bs4 import BeautifulSoup

# ---------------- Config -----------------
MIN_BONUS: int = int(os.getenv("MIN_BONUS", 80))
DEBUG_ALWAYS: bool = os.getenv("DEBUG_ALWAYS", "0").lower() in {"1", "true", "yes"}
TIMEOUT = 25
HEADERS = {"User-Agent": "Mozilla/5.0 (BonusBot)"}
CACHE_FILE = "seen.json"

# fontes RSS (preferência) + fallback feedburner
PROGRAMS: dict[str, list[str]] = {
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
    "Blog – MD bônus": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed",
    ],
    "Blog – Passageiro de Primeira": [
        "https://passageirodeprimeira.com/feed/",
    ],
    "Promo Milhas": [
        "https://promomilhas.com.br/feed/",
    ],
}

PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
]

BONUS_RE = re.compile(r"(?P<pct>\d{2,3})\s*%[^%]*?\b(bônus|bonus)[^%]*?\btransf", re.I)

# --------- Telegram -------------
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TG_CHAT = os.getenv("TELEGRAM_CHAT_ID", "")
TG_URL = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"

def send_telegram(msg: str) -> None:
    if not TG_TOKEN or not TG_CHAT:
        print("[TG] skipping – token/chat not set")
        return
    payload = {"chat_id": TG_CHAT, "text": msg, "disable_web_page_preview": True}
    r = requests.post(TG_URL, data=payload, timeout=15)
    print("[TG]", r.status_code, r.text[:120])
    r.raise_for_status()

# ---------- Cache de alertas ------------
try:
    with open(CACHE_FILE) as f:
        SEEN: set[str] = set(json.load(f))
except Exception:
    SEEN = set()

def save_cache():
    with open(CACHE_FILE, "w") as f:
        json.dump(list(SEEN), f)

# ---------- Fetch helpers --------------

def fetch_url(url: str) -> str | None:
    try:
        return requests.get(url, headers=HEADERS, timeout=TIMEOUT).text
    except Exception as e:
        print(f"[WARN] direto falhou {url} → {e}")
        for tpl in PROXY_TPL:
            purl = tpl.format(u=url)
            try:
                html = requests.get(purl, headers=HEADERS, timeout=TIMEOUT).text
                print(f"[INFO] via proxy OK → {purl[:60]}…")
                return html
            except Exception as pe:
                print(f"[WARN] proxy falhou {purl[:60]}… → {pe}")
        return None

# ---------- Core --------------

def parse_feed(src: str, html: str):
    feed = feedparser.parse(html)
    for entry in feed.entries:
        txt = f"{entry.get('title','')} {entry.get('summary','')[:300]}"
        m = BONUS_RE.search(txt)
        if m:
            pct = int(m.group("pct"))
            if pct >= MIN_BONUS or DEBUG_ALWAYS:
                link = entry.get("link") or "(sem link)"
                sig = f"{pct}|{link.split('?')[0]}"
                if sig in SEEN:
                    continue
                SEEN.add(sig)
                msg = f"📣 {pct}% · {src}\n{link}"
                send_telegram(msg)


def main():
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for src, urls in PROGRAMS.items():
        for url in urls:
            html = fetch_url(url)
            if not html:
                continue
            if url.endswith(".rss") or url.endswith("/feed") or "feed" in url:
                parse_feed(src, html)
            else:
                # Fallback: extrair % no HTML bruto
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text(" ", strip=True)[:500]
                m = BONUS_RE.search(text)
                if m:
                    pct = int(m.group("pct"))
                    if pct >= MIN_BONUS or DEBUG_ALWAYS:
                        sig = f"{pct}|{url}"
                        if sig in SEEN:
                            continue
                        SEEN.add(sig)
                        msg = f"📣 {pct}% · {src} → abrir"
                        send_telegram(msg)
            time.sleep(0.5)  # educado
    save_cache()
    print("[INFO] Varredura concluída.")

if __name__ == "__main__":
    main()
