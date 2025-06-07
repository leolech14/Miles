from __future__ import annotations

from urllib.parse import urlparse, parse_qs, unquote, quote_plus

import yaml
import requests
from bs4 import BeautifulSoup, Tag

from bonus_alert_bot import send_telegram, HEADERS, SOURCES_PATH


QUERY = "transferencia de pontos bonus milhas"


def _extract_urls(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls: list[str] = []
    for a in soup.find_all("a", href=True):
        if isinstance(a, Tag):  # Ensure 'a' is a Tag
            href = a["href"]
            if isinstance(href, str):  # Ensure 'href' is a string
                if "duckduckgo.com" in urlparse(href).netloc:
                    q = parse_qs(urlparse(href).query).get("uddg")
                    if (
                        isinstance(q, list) and q and isinstance(q[0], str)
                    ):  # Validate 'q'
                        href = unquote(q[0])
                parsed = urlparse(href)
                if parsed.scheme.startswith("http") and parsed.netloc:
                    url = f"https://{parsed.netloc}"
                    urls.append(url)
    return urls


def search_new_sources() -> list[str]:
    url = f"https://duckduckgo.com/html/?q={quote_plus(QUERY)}"
    try:
        html = requests.get(url, headers=HEADERS, timeout=15).text
    except Exception:
        return []
    return _extract_urls(html)


def update_sources() -> list[str]:
    try:
        with open(SOURCES_PATH) as f:
            current: list[str] = yaml.safe_load(f)
    except FileNotFoundError:
        current = []
    existing = set(current)
    found: list[str] = []
    for url in search_new_sources():
        if url not in existing:
            current.append(url)
            existing.add(url)
            found.append(url)
    if found:
        with open(SOURCES_PATH, "w") as f:
            yaml.safe_dump(current, f, sort_keys=False)
        try:
            send_telegram("Novas fontes adicionadas:\n" + "\n".join(found))
        except Exception:
            pass
    return found
