#!/usr/bin/env python3
"""
Bonus Alert Bot • v2.4.1  (29 May 2025)
=======================================
Detecta promoções de **bônus de transferência** de pontos e avisa no Telegram.
Agora reconhece também textos que anunciem bônus como “em **dobro**”, “**2x**” etc.

Principais parâmetros ------------------------------------------------------
MIN_BONUS      = 80     # % mínimo. Ignorado se encontrar "dobro/2x".
DEBUG_ALWAYS   = False  # True ➜ envia ping mesmo sem bônus.

Como funciona --------------------------------------------------------------
1. Lê RSS/HTML das URLs em PROGRAMS.
2. Para cada item → `title + summary` (≤300 chars).
3. Detecta promo se:
   • Regex pct/keyword encontra % **e** "bônus … transfer*"; ou
   • Regex FOBRO encontra "dobro|2x" **e** palavra‑raiz "transfer".
4. Se pct < MIN_BONUS → descarta.
5. Evita duplicatas via cache `seen.json`.
6. Envia mensagem condensada e loga resultado do Telegram.

"""
import os, re, json, time, warnings, hashlib, requests, feedparser
from bs4 import BeautifulSoup

# ======================= Config =======================
MIN_BONUS      = int(os.getenv("MIN_BONUS", 80))
DEBUG_ALWAYS   = os.getenv("DEBUG_ALWAYS", "False").lower() == "true"
CACHE_FILE     = "seen.json"
TIMEOUT        = 25
HEADERS        = {"User-Agent": "Mozilla/5.0 BonusAlertBot"}

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
    "MD – Transferência bônus": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed",
    ],
    "Promo Milhas": [
        "https://promomilhas.com.br/feed/",
    ],
    "Passageiro de Primeira": [
        "https://passageirodeprimeira.com/feed/",
    ],
}

PROXY_TPL = [
    "https://api.allorigins.win/raw?url={u}",
]

# ======================= Utilidades ===================
PERC_RE = re.compile(r"(?P<pct>\d{2,3})\s*%", re.I)
FULL_RE = re.compile(r"(?P<pct>\d{2,3})\s*%.*?(bônus|bonus).*?transf(er|ê)nci", re.I)
DOBRO_RE = re.compile(r"\b(dobro|dobrar|duplicar|2x)\b.*?transf", re.I)

def load_cache():
    try:
        with open(CACHE_FILE, "r") as f:
            return set(json.load(f))
    except FileNotFoundError:
        return set()

def save_cache(cache):
    with open(CACHE_FILE, "w") as f:
        json.dump(list(cache), f)

seen = load_cache()

def hash_sig(text: str) -> str:
    return hashlib.md5(text.encode()).hexdigest()

# ======================= Fonte → HTML/RSS =============

def fetch_url(url: str) -> str | None:
    try:
        return requests.get(url, headers=HEADERS, timeout=TIMEOUT).text
    except Exception:
        for tpl in PROXY_TPL:
            try:
                proxy_url = tpl.format(u=url)
                return requests.get(proxy_url, headers=HEADERS, timeout=TIMEOUT).text
            except Exception:
                continue
    return None

# ======================= Parsing ======================

def analyse_text(src: str, text: str, link: str):
    m = FULL_RE.search(text)
    if m:
        pct = int(m.group("pct"))
    else:
        if DOBRO_RE.search(text):
            pct = 100  # padrão para "dobro/2x"
        else:
            return
    if pct < MIN_BONUS and not DEBUG_ALWAYS:
        return
    sig = hash_sig(f"{pct}|{link}")
    if sig in seen:
        return
    seen.add(sig)
    msg = f"📣 {pct}% · {src} → {link}"
    send_telegram(msg)

# ======================= Telegram =====================

def send_telegram(msg: str):
    tok  = os.environ["TELEGRAM_BOT_TOKEN"]
    chat = os.environ["TELEGRAM_CHAT_ID"]
    url  = f"https://api.telegram.org/bot{tok}/sendMessage"
    r = requests.post(url, data={"chat_id": chat, "text": msg, "disable_web_page_preview": True}, timeout=15)
    print("[TG]", r.status_code, r.text[:120])
    r.raise_for_status()

# ======================= Main =========================

def run():
    for src, urls in PROGRAMS.items():
        for u in urls:
            raw = fetch_url(u)
            if not raw:
                continue
            if u.endswith((".rss", ".xml")):
                feed = feedparser.parse(raw)
                for e in feed.entries:
                    link = e.get("link")
                    text = (e.get("title", "") + " " + e.get("summary", ""))[:300]
                    analyse_text(src, text, link)
            else:
                soup = BeautifulSoup(raw, "html.parser")
                title = soup.title.text if soup.title else ""
                analyse_text(src, title + " " + soup.get_text(" ")[:300], u)

    save_cache(seen)

if __name__ == "__main__":
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    t0 = time.time()
    run()
    print(f"[INFO] Duration {time.time()-t0:.1f}s")
