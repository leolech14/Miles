"""Source Discovery Plugin - AI-powered mileage source finder."""

from datetime import datetime
from typing import List
from urllib.parse import urlparse, parse_qs, unquote, quote_plus

import requests
from bs4 import BeautifulSoup, Tag

from miles.plugin_api import Promo
from miles.source_store import SourceStore


class SourceDiscoveryPlugin:
    """AI-powered source discovery plugin."""

    name = "source-discovery"
    schedule = "0 7 * * *"  # Daily at 7 AM
    categories = ["discovery"]

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.query = "transferencia de pontos bonus milhas"

    def scrape(self, since: datetime) -> List[Promo]:
        """Discover new mileage sources and add them to the store."""
        try:
            new_sources = self._search_new_sources()
            added_sources = self._update_source_store(new_sources)

            # Convert added sources to Promo format for notification
            promos = []
            for source in added_sources:
                promos.append(
                    Promo(
                        program="SOURCE_DISCOVERY",
                        bonus_pct=0,  # Not a bonus, but a new source
                        start_dt=None,
                        end_dt=None,
                        url=source,
                        title=f"🔍 New mileage source discovered: {urlparse(source).netloc}",
                        source=self.name,
                    )
                )

            return promos

        except Exception as e:
            print(f"[{self.name}] Error during source discovery: {e}")
            return []

    def _search_new_sources(self) -> List[str]:
        """Search for new sources using DuckDuckGo."""
        url = f"https://duckduckgo.com/html/?q={quote_plus(self.query)}"
        try:
            response = requests.get(url, headers=self.headers, timeout=15)
            return self._extract_urls(response.text)
        except Exception:
            return []

    def _extract_urls(self, html: str) -> List[str]:
        """Extract URLs from search results."""
        soup = BeautifulSoup(html, "html.parser")
        urls: List[str] = []

        for a in soup.find_all("a", href=True):
            if isinstance(a, Tag):
                href = a["href"]
                if isinstance(href, str):
                    # Handle DuckDuckGo redirects
                    if "duckduckgo.com" in urlparse(href).netloc:
                        q = parse_qs(urlparse(href).query).get("uddg")
                        if isinstance(q, list) and q and isinstance(q[0], str):
                            href = unquote(q[0])

                    parsed = urlparse(href)
                    if parsed.scheme.startswith("http") and parsed.netloc:
                        url = f"https://{parsed.netloc}"
                        urls.append(url)
        return urls

    def _update_source_store(self, search_results: List[str]) -> List[str]:
        """Update source store with new relevant sources."""
        store = SourceStore()
        current = store.all()
        existing = set(current)
        found: List[str] = []

        print(
            f"[{self.name}] Found {len(search_results)} potential sources from search"
        )

        # Filter out existing sources and add relevant ones
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
                        "livelo",
                        "destinos",
                        "passageiro",
                    ]
                ):
                    if store.add(url):
                        found.append(url)
                        print(f"[{self.name}] Added new source: {url}")
                    else:
                        print(f"[{self.name}] Failed to add source: {url}")

        if found:
            print(f"[{self.name}] Successfully added {len(found)} new sources")
        else:
            print(
                f"[{self.name}] No new sources found (checked {len(search_results)} candidates)"
            )

        return found
