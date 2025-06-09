from __future__ import annotations

import os
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests
from bs4 import BeautifulSoup, Tag

from miles.bonus_alert_bot import HEADERS, send_telegram

SOURCES_PATH = os.getenv("SOURCES_PATH", "sources.yaml")


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
    from miles.source_store import SourceStore

    # Get current sources from SourceStore instead of YAML directly
    store = SourceStore()
    current = store.all()
    existing = set(current)
    found: list[str] = []

    # Search for new sources
    search_results = search_new_sources()
    print(
        f"[source_search] Found {len(search_results)} potential sources from DuckDuckGo"
    )

    # Filter out existing sources
    for url in search_results:
        if url not in existing:
            # Additional filtering for mileage-related domains
            domain = url.lower()
            if any(
                keyword in domain
                for keyword in [
                    "milhas",
                    "miles",
                    "pontos",
                    "smiles",
                    "azul",
                    "latam",
                    "gol",
                ]
            ):
                if store.add(url):  # Use SourceStore to add
                    found.append(url)
                    print(f"[source_search] Added new source: {url}")
                else:
                    print(f"[source_search] Failed to add source: {url}")

    if found:
        try:
            send_telegram(
                f"🔍 Found {len(found)} new mileage sources:\n" + "\n".join(found)
            )
        except Exception as e:
            print(f"[source_search] Failed to send telegram: {e}")
    else:
        print(
            f"[source_search] No new sources found (checked {len(search_results)} candidates)"
        )

    return found
