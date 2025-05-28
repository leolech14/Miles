#!/usr/bin/env python3
"""
Bonus Alert Bot – versão 2.0 · 28‑Mai‑2025
-------------------------------------------------
• Escaneia bônus de transferência (≥ MIN_BONUS, default 100 %) em múltiplas fontes.
• **Duas camadas** de coleta:
    1. Fetch direto (HTML/RSS).
    2. Se falhar, tenta via proxies simples (texto): r.jina.ai e allorigins.
• Cabeçalho UA, time‑outs, log clean, Telegram alert Markdown.

Edite no topo:
  MIN_BONUS     = 100      # % mínimo para alertar
  PROXY_ENABLED = True     # ativa camada‑proxy
  SCHEDULE      = hourly   # (workflow já usa cron 0 * * * *)

A workflow YAML não muda – executa de hora em hora.
"""
from __future__ import annotations
import os, re, sys, datetime as dt, urllib.parse as up
from typing import List, Dict
import requests, warnings
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
from telegram import Bot

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

###################### CONFIG ###########################
MIN_BONUS     = int(os.getenv("MIN_BONUS", "50"))
PROXY_ENABLED = os.getenv("PROXY_ENABLED", "1") != "0"
TIMEOUT       = 25
HEADERS       = {"User-Agent": "Mozilla/5.0 BonusAlertBot/2.0"}

PROGRAMS: Dict[str, List[str]] = {
    # Cias – usar página fallback RSS primeiro
    "Smiles": [
        "https://feeds.feedburner.com/PromocoesSmiles",
        "https://www.smiles.com.br/promocoes/bancos"
    ],
    "LATAM": [
        "https://feeds.feedburner.com/PromocoesLatamPass",
        "https://www.latam.com/latam-pass/pt_br/novidades/promocoes"
    ],
    "TudoAzul": [
        "https://feeds.feedburner.com/PromocoesTudoAzul",
        "https://tudoazul.voeazul.com.br/portal/pt/ofertas"
    ],
    # Blogs / agregadores
    "MelhoresDestinos": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus/feed"
    ],
    "PassageiroDePrimeira": [
        "https://passageirodeprimeira.com/feed/"
    ],
    "PromoMilhasForum": [
        "https://promomilhas.com.br/feed/"
    ]
}

# Proxies simples que retornam texto puro
PROXY_TPL = [
    "https://r.jina.ai/http://{u}",
    "https://api.allorigins.win/raw?url={enc}"
]
#########################################################

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT:
    sys.exit("[FATAL] TELEGRAM_BOT_TOKEN ou CHAT_ID não definido.")

bot = Bot(token=TOKEN)
RE_BONUS = re.compile(r"(\d{2,3})\s*%", re.I)

###################### CORE #############################

def http_get(url: str) -> str | None:
    """Requisição simples com UA e timeout."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] {url} falhou: {e}")
        return None


def fetch_with_proxy(original_url: str) -> str | None:
    """Tenta obter o conteúdo via proxies de texto."""
    if not PROXY_ENABLED:
        return None
    for tpl in PROXY_TPL:
        prox_url = tpl.replace("{u}", original_url).replace("{enc}", up.quote_plus(original_url))
        html = http_get(prox_url)
        if html:
            print(f"[INFO] proxy ok → {prox_url[:60]}…")
            return html
    return None


def get_html(urls: List[str]) -> str | None:
    """Tenta direto, depois via proxy se necessário."""
    for u in urls:
        html = http_get(u)
        if html:
            return html
        # fallback via proxy
        html = fetch_with_proxy(u)
        if html:
            return html
    return None


def extract_bonus_pct(text: str) -> List[int]:
    return [int(m.group(1)) for m in RE_BONUS.finditer(text)]


def scan_source(name: str, urls: List[str]):
    html = get_html(urls)
    if not html:
        print(f"[ERROR] {name}: sem acesso às URLs.")
        return
    soup = BeautifulSoup(html, "html.parser")
    bonuses = extract_bonus_pct(soup.get_text(" ", strip=True))
    if not bonuses:
        print(f"[INFO] {name}: nenhum % detectado.")
        return
    top = max(bonuses)
    print(f"[DEBUG] {name}: max {top}%")
    if top >= MIN_BONUS:
        alert(name, top, urls[0])


def alert(source: str, pct: int, link: str):
    msg = (f"📣 *BÔNUS {pct}%* em *{source}*\n"
           f"[Abrir promoção]({link})\n"
           f"_(threshold {MIN_BONUS}% • {dt.datetime.now():%d/%m %H:%M})_")
    try:
        bot.send_message(chat_id=CHAT, text=msg, parse_mode="Markdown")
        print(f"[ALERT] enviado {source} {pct}%")
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")


def main():
    print(f"=== BonusAlertBot v2 busca ≥ {MIN_BONUS}% (proxy={'on' if PROXY_ENABLED else 'off'}) ===")
    for name, urls in PROGRAMS.items():
        scan_source(name, urls)
    print("[INFO] Varredura concluída.")


if __name__ == "__main__":
    main()
