#!/usr/bin/env python3
"""
Bonus Alert Bot – versão 1.2  ·  2025‑05‑28
------------------------------------------
Raspa múltiplas fontes (sites oficiais das cias + blogs confiáveis)
em busca de **bônus de transferência de pontos bancários** iguais ou
acima de um limiar definido (padrão 100 %).  Ao detectar, envia
mensagem via Telegram.

→ Como executar localmente
   export TELEGRAM_BOT_TOKEN="<token>"
   export TELEGRAM_CHAT_ID="<id>"
   python bonus_alert_bot.py

→ No GitHub Actions o token/id vêm de *Secrets*.

Changelog
---------
1.2 • 28‑Mai‑2025  ·  cabeçalho User‑Agent, mais tratativa de erros, novas
     fontes (Melhores Destinos, Passageiro de Primeira) e regex multilingue
1.1 • 28‑Mai‑2025  ·  ajuste URLs LATAM/TudoAzul, timeout global
1.0 • 27‑Mai‑2025  ·  versão inicial
"""
from __future__ import annotations
import os, re, sys, time, datetime as dt
from typing import Iterable
import requests
from bs4 import BeautifulSoup
from telegram import Bot

##############################################################################
# Configuráveis – mude aqui                                                 #
##############################################################################
MIN_BONUS: int = int(os.getenv("MIN_BONUS", "100"))   # avisa se ≥ este valor
TIMEOUT   : int = 30                                   # segs p/ timeout HTTP
HEADERS   = {"User-Agent": "Mozilla/5.0 (BonusAlertBot)"}

# Fontes estáticas que contêm o HTML com o texto do bônus (sem JS pesado)
PROGRAMS: dict[str, str] = {
    # Cias aéreas / bancos
    "Smiles"       : "https://www.smiles.com.br/promocoes/bancos",
    "LATAM"        : "https://www.latam.com/latam-pass/pt_br/novidades/promocoes",
    "TudoAzul"     : "https://tudoazul.voeazul.com.br/portal/pt/ofertas",
    # Blogs de milhas – fazem curadoria das promoções
    "MelhoresDestinos" : "https://www.melhoresdestinos.com.br/tag/transferencia-bonus",
    "PassageiroDePrimeira" : "https://passageirodeprimeira.com/category/promocoes-de-transferencia/"
}

##############################################################################
# Telegram init                                                             #
##############################################################################
try:
    TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    CHAT  = os.environ["TELEGRAM_CHAT_ID"]
except KeyError as e:
    sys.exit(f"[FATAL] Variável de ambiente ausente: {e.args[0]}")

bot = Bot(token=TOKEN)

##############################################################################
# Funções utilitárias                                                       #
##############################################################################
RE_BONUS = re.compile(r"(\d{2,3})\s*%", re.I)

def extract_bonus(text: str) -> Iterable[int]:
    """Devolve lista de inteiros % encontrados."""
    return [int(m.group(1)) for m in RE_BONUS.finditer(text)]


def fetch_html(url: str) -> str | None:
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[WARN] Falha ao baixar {url}: {e}")
        return None


def scan_source(name: str, url: str) -> None:
    html = fetch_html(url)
    if not html:
        return
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)
    bonuses = extract_bonus(text)
    if not bonuses:
        print(f"[INFO] {name}: nenhum número de % encontrado.")
        return
    top = max(bonuses)
    print(f"[DEBUG] {name}: max {top}%")
    if top >= MIN_BONUS:
        send_alert(name, top, url)


def send_alert(source: str, bonus: int, url: str) -> None:
    msg = (
        f"📢 *BÔNUS {bonus}%* detectado em *{source}*\n"
        f"[Abrir promoção]({url})\n\n"
        f"Limite configurado: {MIN_BONUS}%\n"
        f"(enviado {dt.datetime.now():%d/%m %H:%M})"
    )
    try:
        bot.send_message(chat_id=CHAT, text=msg, parse_mode="Markdown")
        print(f"[INFO] Alerta enviado: {source} {bonus}%")
    except Exception as e:
        print(f"[ERROR] Telegram falhou: {e}")

##############################################################################
# Main loop                                                                 #
##############################################################################

def main() -> None:
    print(f"=== Bonus Alert Bot – busca por ≥ {MIN_BONUS}% ===")
    for name, url in PROGRAMS.items():
        scan_source(name, url)
    print("[INFO] varredura concluída.")

if __name__ == "__main__":
    main()
