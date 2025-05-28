#!/usr/bin/env python3
"""
Bonus Alert Bot · v2.1  (28 May 2025)
=====================================
Escaneia fontes HTML/RSS + fallback via proxies em busca de **bônus de transferência**
de pontos bancários para programas de milhas. Quando encontra percentual ≥ MIN_BONUS
(padrão 100 %), envia alerta no Telegram.

Como usar localmente
--------------------
$ export TELEGRAM_BOT_TOKEN="<token>"
$ export TELEGRAM_CHAT_ID="<id>"
$ python bonus_alert_bot.py

No GitHub Actions o workflow injeta as variáveis a partir de *Secrets*.
"""
from __future__ import annotations
import os, re, sys, time, warnings, html
import requests
from bs4 import BeautifulSoup

# -------- CONFIGURÁVEIS ----------------------------
MIN_BONUS     = int(os.getenv("MIN_BONUS", 100))   # % mínimo para alertar
DEBUG_ALWAYS  = os.getenv("DEBUG_ALWAYS", "False").lower() == "true"
TIMEOUT       = int(os.getenv("TIMEOUT", 30))      # segundos
USE_PROXY     = os.getenv("USE_PROXY", "True").lower() != "false"
HEADERS       = {"User-Agent": "Mozilla/5.0 (BonusAlertBot)"}

# Fontes primárias (sempre RSS/HTML plain) ----------
PROGRAMS: dict[str, list[str]] = {
    "Smiles" : [
        "https://www.melhoresdestinos.com.br/tag/smiles/feed",
        "https://feeds.feedburner.com/PromocoesSmiles"
    ],
    "LATAM"  : [
        "https://www.melhoresdestinos.com.br/tag/latam-pass/feed",
        "https://feeds.feedburner.com/PromocoesLatamPass"
    ],
    "TudoAzul" : [
        "https://www.melhoresdestinos.com.br/tag/tudoazul/feed",
        "https://feeds.feedburner.com/PromocoesTudoAzul"
    ],
    "Blogs" : [
        "https://passageirodeprimeira.com/feed/",
        "https://www.melhoresdestinos.com.br/feed"
    ],
}

# Proxies text‑only (tentados na ordem)
PROXY_TPL: list[str] = [
    "https://r.jina.ai/http://{u}",
    "https://api.allorigins.win/raw?url={u}"
]
# ---------------------------------------------------

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")
if not (TOKEN and CHAT):
    sys.exit("[FATAL] TELEGRAM_BOT_TOKEN e CHAT_ID não definidos")

tg_api = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

warnings.filterwarnings("ignore", category=UserWarning)  # suprime XMLParsedAsHTMLWarning

RE_PERCENT = re.compile(r"(\d{2,3})\s*%")


def fetch_raw(url: str) -> str | None:
    """Tenta baixar URL. Retorna texto ou None ao falhar."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] {url} falhou: {e}")
        return None


def fetch_with_proxy(url: str) -> str | None:
    if not USE_PROXY:
        return None
    for tpl in PROXY_TPL:
        purl = tpl.format(u=url)
        txt  = fetch_raw(purl)
        if txt:
            print(f"[INFO] Proxy OK → {purl}")
            return txt
    return None


def extract_bonus(html_text: str) -> int | None:
    """Retorna maior percent encontrado (int) ou None."""
    matches = [int(m.group(1)) for m in RE_PERCENT.finditer(html_text)]
    return max(matches) if matches else None


def send_alert(source: str, pct: int, link: str):
    txt = f"📣 *{pct}%* | *{source}* → [abrir]({html.escape(link, quote=True)})"
    requests.post(tg_api, data={
        "chat_id": CHAT,
        "text": txt,
        "parse_mode": "Markdown",
        "disable_web_page_preview": True,
    }, timeout=15)


def main():
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for source, urls in PROGRAMS.items():
        pct_found = None
        good_link = None
        for u in urls:
            html_txt = fetch_raw(u) or fetch_with_proxy(u)
            if not html_txt:
                continue
            pct = extract_bonus(html_txt)
            if pct is not None:
                pct_found, good_link = pct, u
                break  # pega primeiro hit
        if pct_found is not None and (pct_found >= MIN_BONUS or DEBUG_ALWAYS):
            send_alert(source, pct_found, good_link or urls[0])
            print(f"[SEND] {source} {pct_found}% → Telegram")
        else:
            print(f"[INFO] {source}: max {pct_found or 'n/a'}%")
    print("[INFO] Varredura concluída.")


if __name__ == "__main__":
    t0 = time.time()
    try:
        main()
    finally:
        print(f"[INFO] Execução em {time.time()-t0:.1f}s")
