"""Smiles Program Monitor Plugin."""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from miles.plugin_api import Promo


class SmilesMonitorPlugin:
    """Monitor Smiles program for transfer bonuses."""

    name = "smiles-monitor"
    schedule = "0 */4 * * *"  # Every 4 hours
    categories = ["bonus", "smiles"]

    def __init__(self) -> None:
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.sources = [
            "https://promocao.smiles.com.br",
            "https://www.smiles.com.br/promocoes",
            "https://melhoresdestinos.com.br/tag/smiles/",
            "https://passageirodeprimeira.com/tag/smiles/",
        ]

    def scrape(self, since: datetime) -> list[Promo]:
        """Scan Smiles-related sources for bonus promotions."""
        promos = []

        for source_url in self.sources:
            try:
                content = self._fetch_content(source_url)
                if content:
                    source_promos = self._parse_smiles_content(content, source_url)
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

    def _parse_smiles_content(self, content: str, source_url: str) -> list[Promo]:
        """Parse content for Smiles bonus promotions."""
        promos = []
        soup = BeautifulSoup(content, "html.parser")

        # Look for bonus patterns in text
        text_content = soup.get_text().lower()

        # Smiles-specific bonus patterns
        patterns = [
            r"smiles.*?(\d+)%.*?b[oô]nus",
            r"transfer.*?smiles.*?(\d+)%",
            r"(\d+)%.*?b[oô]nus.*?smiles",
            r"livelo.*?smiles.*?(\d+)%",
            r"(\d+)%.*?livelo.*?smiles",
        ]

        found_bonuses = set()  # Avoid duplicates

        for pattern in patterns:
            matches = re.finditer(pattern, text_content)
            for match in matches:
                try:
                    bonus_pct = int(match.group(1))
                    if (
                        bonus_pct >= 50 and bonus_pct not in found_bonuses
                    ):  # Filter meaningful bonuses
                        found_bonuses.add(bonus_pct)

                        # Extract title from surrounding context
                        start = max(0, match.start() - 100)
                        end = min(len(text_content), match.end() + 100)
                        context = text_content[start:end].strip()

                        # Clean up the title
                        title = self._clean_title(context, bonus_pct)

                        promos.append(
                            Promo(
                                program="SMILES",
                                bonus_pct=bonus_pct,
                                start_dt=None,  # Would need more parsing for dates
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
            if str(bonus_pct) in sentence and "smiles" in sentence.lower():
                title = sentence.strip()
                if len(title) > 10:  # Ensure meaningful content
                    return f"✈️ {title[:100]}..."

        # Fallback title
        return f"✈️ Smiles {bonus_pct}% transfer bonus detected"
