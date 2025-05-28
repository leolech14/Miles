#!/usr/bin/env python3
"""
Bonus Alert Bot – versão 1.3  ·  28‑Mai‑2025
-------------------------------------------
* Busca bônus de transferência (≥ MIN_BONUS, default 100 %) em **10 fontes**
  – sites oficiais das 3 cias + 7 blogs/canais que publicam promo em tempo real.
* Tenta múltiplos URLs por companhia (cai para fallback se 404).
* Cabeçalho UA, timeout, parsing regex, Telegram alerta markdown.

Edite no topo:
  MIN_BONUS   = 100   # % mínimo para alertar
  PROGRAMS    = {...} # acrescente novas fontes quando quiser
"""
from __future__ import annotations
import os, re, sys, datetime as dt
from typing import Iterable, List, Dict
import requests
from bs4 import BeautifulSoup
from telegram import Bot

###################### CONFIG ###########################
MIN_BONUS: int = int(os.getenv("MIN_BONUS", "100"))
TIMEOUT   : int = 25  # segundos
HEADERS   = {"User-Agent": "Mozilla/5.0 BonusAlertBot"}

# Cada chave tem lista de URLs (ordem de tentativa)
PROGRAMS: Dict[str, List[str]] = {
    # ---------- Cias aéreas ----------
    "Smiles": [
        "https://www.smiles.com.br/promocoes/bancos",
        "https://www.smiles.com.br/promocoes/pontos-bancos"  # legacy
    ],
    "LATAM": [
        "https://www.latam.com/latam-pass/pt_br/novidades/promocoes",
        "https://www.latam.com/latam-pass/pt_br/promocoes/bancos"
    ],
    "TudoAzul": [
        "https://tudoazul.voeazul.com.br/portal/pt/ofertas",
        "https://tudoazul.voeazul.com.br/promocoes"
    ],
    # ---------- Blogs & canais de alerta ----------
    "MelhoresDestinos": [
        "https://www.melhoresdestinos.com.br/tag/transferencia-bonus"
    ],
    "PassageiroDePrimeira": [
        "https://passageirodeprimeira.com/category/promocoes-de-transferencia/"
    ],
    "PromoMilhasForum": [
        "https://promomilhas.com.br/categoria/promocao-transferencia/"
    ],
    "MD_PromoPage": [
        "https://www.melhoresdestinos.com.br/promocoes-de-pontos-e-milhas"
    ],
    "PP_TelegramMirror": [
        "https://passageirodeprimeira.com/feed/"  # RSS como HTML simples
    ]
}
#########################################################

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT  = os.getenv("TELEGRAM_CHAT_ID")
if not TOKEN or not CHAT:
    sys.exit("[FATAL] TELEGRAM_BOT_TOKEN ou CHAT_ID não definido.")

bot = Bot(token=TOKEN)
RE_BONUS = re.compile(r"(\d{2,3})\s*%", re.I)

def fetch_first_html(urls: List[str]) -> str | None:
    """Tenta cada URL até obter HTML válido (status 200)."""
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
            r.raise_for_status()
            return r.text
        except Exception as e:
            print(f"[WARN] {url} falhou: {e}")
    return None

def extract_bonus_pct(text: str) -> List[int]:
    return [int(m.group(1)) for m in RE_BONUS.finditer(text)]

def scan_source(name: str, urls: List[str]):
    html = fetch_first_html(urls)
    if not html:
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
           f"(min configurado {MIN_BONUS}% – {dt.datetime.now():%d/%m %H:%M})")
    try:
        bot.send_message(chat_id=CHAT, text=msg, parse_mode="Markdown")
        print(f"[ALERT] enviado {source} {pct}%")
    except Exception as e:
        print(f"[ERROR] Telegram: {e}")

def main():
    print(f"=== BonusAlertBot busca ≥ {MIN_BONUS}% ===")
    for name, urls in PROGRAMS.items():
        scan_source(name, urls)
    print("[INFO] Varredura concluída.")

if __name__ == "__main__":
    main()
