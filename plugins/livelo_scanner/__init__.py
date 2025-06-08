"""Livelo Program Scanner Plugin."""

from datetime import datetime
from typing import List
import re
import requests
from bs4 import BeautifulSoup

from miles.plugin_api import Promo


class LiveloScannerPlugin:
    """Monitor Livelo program for transfer bonuses."""

    name = "livelo-scanner"
    schedule = "0 */6 * * *"  # Every 6 hours
    categories = ["bonus", "livelo"]

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.sources = [
            "https://www.livelo.com.br/promocoes",
            "https://melhoresdestinos.com.br/tag/livelo/",
            "https://passageirodeprimeira.com/tag/livelo/",
            "https://mestredasmilhas.com/tag/livelo/",
        ]

    def scrape(self, since: datetime) -> List[Promo]:
        """Scan Livelo-related sources for bonus promotions."""
        promos = []

        for source_url in self.sources:
            try:
                content = self._fetch_content(source_url)
                if content:
                    source_promos = self._parse_livelo_content(content, source_url)
                    promos.extend(source_promos)
            except Exception as e:
                print(f"[{self.name}] Error scanning {source_url}: {e}")

        return promos

    def _fetch_content(self, url: str) -> str | None:
        """Fetch content from URL."""
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"[{self.name}] Failed to fetch {url}: {e}")
            return None

    def _parse_livelo_content(self, content: str, source_url: str) -> List[Promo]:
        """Parse content for Livelo bonus promotions."""
        promos = []
        soup = BeautifulSoup(content, "html.parser")

        # Look for bonus patterns in text
        text_content = soup.get_text().lower()

        # Livelo-specific bonus patterns
        patterns = [
            r"livelo.*?(\d+)%.*?b[oô]nus",
            r"transfer.*?livelo.*?(\d+)%",
            r"(\d+)%.*?b[oô]nus.*?livelo",
            r"banco.*?livelo.*?(\d+)%",
            r"cart[aã]o.*?livelo.*?(\d+)%",
            r"livelo.*?smiles.*?(\d+)%",
        ]

        found_bonuses = set()  # Avoid duplicates

        for pattern in patterns:
            matches = re.finditer(pattern, text_content)
            for match in matches:
                try:
                    bonus_pct = int(match.group(1))
                    if (
                        bonus_pct >= 30 and bonus_pct not in found_bonuses
                    ):  # Lower threshold for Livelo
                        found_bonuses.add(bonus_pct)

                        # Extract title from surrounding context
                        start = max(0, match.start() - 150)
                        end = min(len(text_content), match.end() + 150)
                        context = text_content[start:end].strip()

                        # Clean up the title
                        title = self._clean_title(context, bonus_pct)

                        promos.append(
                            Promo(
                                program="LIVELO",
                                bonus_pct=bonus_pct,
                                start_dt=None,
                                end_dt=None,
                                url=source_url,
                                title=title,
                                source=self.name,
                            )
                        )

                except (ValueError, IndexError):
                    continue

        return promos

    def _clean_title(self, context: str, bonus_pct: int) -> str:
        """Clean and format the promotion title."""
        # Remove extra whitespace and newlines
        context = re.sub(r"\s+", " ", context).strip()

        # Try to extract a meaningful title
        sentences = context.split(".")
        for sentence in sentences:
            if str(bonus_pct) in sentence and "livelo" in sentence.lower():
                title = sentence.strip()
                if len(title) > 10:
                    return f"🎯 {title[:100]}..."

        # Fallback title
        return f"🎯 Livelo {bonus_pct}% transfer bonus detected"
