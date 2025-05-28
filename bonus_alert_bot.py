#!/usr/bin/env python3
"""
Bonus Alert Bot • v2.5  (29 May 2025)
======================================
> *Modo de teste* — roda a cada 2 h e SEMPRE envia um ping (DEBUG_ALWAYS = True)
> assim validamos entrega e parsing. Ajuste depois para produção.

• Fontes reformuladas → feeds estáveis FeedBurner/WordPress + oficiais:
    – Smiles, LATAM Pass, TudoAzul (feeds Melhores Destinos segmentados)
    – Feeds oficiais Smiles & LATAM Pass
    – MD tag "transferencia-bonus", Passageiro de Primeira, Promomilhas
• Regex inteligente → detecta "NN % bônus transferência" ou "☑ dobro/2x transfer".
• Cache visto em `seen.json` evita duplicatas.

"""
from __future__ import annotations
import os, re, json, time, hashlib, warnings, requests, feedparser
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

# ------------- CONFIGURAÇÃO PRINCIPAL -----------------
MIN_BONUS      = int(os.getenv("MIN_BONUS", 80))   # exige 80 %+ (ignorado se dobro)
DEBUG_ALWAYS   = os.getenv("DEBUG_ALWAYS", "True") == "True"  # envia ping teste
TIMEOUT        = 25

PROGRAMS: dict[str, list[str]] = {
    "Smiles": [
        "https://feeds.feedburner.com/melhoresdestinos-smiles",
        "https://www.smiles.com.br/feed",
    ],
    "LATAM Pass": [
        "https://feeds.feedburner.com/melhoresdestinos-latampass",
        "https://www.latam.com/latam-pass/feed",
    ],
    "TudoAzul": [
        "https://feeds.feedburner.com/melhoresdestinos-tudoazul",
    ],
    "MD – Transferência bônus": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed",
    ],
    "Passageiro de Primeira": [
        "https://passageirodeprimeira.com/feed/",
    ],
    "Promo Milhas": [
        "https://promomilhas.com.br/feed/",
    ],
}

HEADERS = {"User-Agent": "Mozilla/5.0 (BonusAlertBot)"}
PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
    "https://r.jina.ai/http://{u}",
]

BONUS_RE = re.compile(r"(?P<pct>\d{2,3})\s*%.*?(bônus|bonus).*?transf", re.I)
DOBRO_RE = re.compile(r"\b(dobro|dobrar|2x|duplicar)\b.*?transf", re.I)

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

def parse_feed(name: str, url: str, seen: set[str], alerts: list[tuple[int,str,str]]):
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

def handle_text(src: str, text: str, link: str, seen: set[str], alerts: list[tuple[int,str,str]]):
    m = BONUS_RE.search(text)
    pct = int(m.group("pct")) if m else None
    if not pct and DOBRO_RE.search(text):
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
    chat  = os.environ["TELEGRAM_CHAT_ID"]
    url   = f"https://api.telegram.org/bot{token}/sendMessage"
    r = requests.post(url, data={
        "chat_id": chat,
        "text": msg,
        "disable_web_page_preview": True,
    }, timeout=15)
    print("[TG]", r.status_code, r.text[:120])
    r.raise_for_status()

# ----------------- MAIN ----------------------------

def main():
    start = time.time()
    seen = load_seen()
    alerts: list[tuple[int,str,str]] = []

    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for src, urls in PROGRAMS.items():
        for url in urls:
            parse_feed(src, url, seen, alerts)

    if DEBUG_ALWAYS and not alerts:
        alerts.append((0, "Debug", "https://example.com"))

    for pct, src, link in alerts:
        msg = f"📣 {pct} % · {src}\n{link}"
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
