"""AI-Powered Source Discovery for Miles Bot

This module uses OpenAI to intelligently discover and validate mileage program sources.
It replaces the basic DuckDuckGo search with advanced AI reasoning.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, cast
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

from miles.bonus_alert_bot import HEADERS, send_telegram
from miles.source_store import SourceStore

logger = logging.getLogger("miles.ai_source_discovery")


class AISourceDiscovery:
    """AI-powered source discovery engine"""

    def __init__(self) -> None:
        self.openai_client = self._get_openai_client()
        self.store = SourceStore()

    def _get_openai_client(self) -> OpenAI | None:
        """Get OpenAI client if available"""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or api_key == "not_set":
            logger.warning(
                "OpenAI API key not available - falling back to basic search"
            )
            return None
        return OpenAI(api_key=api_key)

    def generate_search_queries(self) -> list[str]:
        """Use AI to generate intelligent search queries for Brazilian mileage sources"""
        if not self.openai_client:
            return ["transferencia de pontos bonus milhas brasil"]

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in Brazilian mileage programs and loyalty points. Generate search queries to find websites that publish transfer bonus promotions.",
                    },
                    {
                        "role": "user",
                        "content": """Generate 5 specific search queries in Portuguese to find Brazilian websites that publish mileage transfer bonus promotions.

Focus on:
- Transfer bonus alerts (bônus de transferência)
- Mileage program news sites
- Points and miles blogs
- Promotion aggregators

Return only the search queries, one per line.""",
                    },
                ],
                temperature=0.7,
                max_tokens=300,
            )

            content = response.choices[0].message.content
            if content:
                queries = content.strip().split("\n")
                # Clean up and filter queries
                clean_queries = [
                    q.strip().strip('"').strip("'") for q in queries if q.strip()
                ]
                logger.info(f"Generated {len(clean_queries)} AI search queries")
                return clean_queries[:5]  # Limit to 5 queries
            return ["transferencia de pontos bonus milhas brasil"]

        except Exception as e:
            logger.error(f"AI query generation failed: {e}")
            return ["transferencia de pontos bonus milhas brasil"]

    def search_multiple_engines(self, queries: list[str]) -> list[str]:
        """Search multiple engines with different queries"""
        all_urls = set()

        for query in queries:
            # DuckDuckGo search
            try:
                ddg_urls = self._search_duckduckgo(query)
                all_urls.update(ddg_urls)
                logger.info(f"DuckDuckGo found {len(ddg_urls)} URLs for: {query}")
            except Exception as e:
                logger.error(f"DuckDuckGo search failed for '{query}': {e}")

            # Bing search
            try:
                bing_urls = self._search_bing(query)
                all_urls.update(bing_urls)
                logger.info(f"Bing found {len(bing_urls)} URLs for: {query}")
            except Exception as e:
                logger.error(f"Bing search failed for '{query}': {e}")

        return list(all_urls)

    def _search_duckduckgo(self, query: str) -> list[str]:
        """Search DuckDuckGo for sources"""
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            return self._extract_urls_from_html(response.text)
        except Exception:
            return []

    def _search_bing(self, query: str) -> list[str]:
        """Search Bing for sources"""
        url = f"https://www.bing.com/search?q={quote_plus(query)}"
        try:
            response = requests.get(url, headers=HEADERS, timeout=15)
            return self._extract_urls_from_html(response.text)
        except Exception:
            return []

    def _extract_urls_from_html(self, html: str) -> list[str]:
        """Extract URLs from search result HTML"""
        soup = BeautifulSoup(html, "html.parser")
        urls = set()

        for link in soup.find_all("a", href=True):
            if hasattr(link, "get"):
                href_value = link.get("href")
                if isinstance(href_value, str):
                    href = href_value
                    # Clean up search engine redirects
                    if "duckduckgo.com" in href and "uddg=" in href:
                        from urllib.parse import parse_qs, unquote

                        try:
                            parsed = urlparse(href)
                            uddg = parse_qs(parsed.query).get("uddg", [])
                            if uddg:
                                href = unquote(uddg[0])
                        except Exception:
                            continue

                    # Extract domain
                    parsed = urlparse(href)
                    if parsed.scheme.startswith("http") and parsed.netloc:
                        domain_url = f"https://{parsed.netloc}"
                        urls.add(domain_url)

        return list(urls)

    def ai_validate_source(self, url: str) -> dict[str, Any]:
        """Use AI to validate if a source is relevant for mileage tracking"""
        if not self.openai_client:
            # Fallback to basic validation
            return self._basic_validate_source(url)

        try:
            # Fetch page content
            response = requests.get(url, headers=HEADERS, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            # Extract text content (first 2000 chars)
            text_content = soup.get_text()[:2000]
            page_title = soup.title.string if soup.title else ""

            # AI analysis
            ai_response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert analyzer of Brazilian mileage and loyalty program websites. Analyze if a website publishes transfer bonus promotions.",
                    },
                    {
                        "role": "user",
                        "content": f"""Analyze this website content:

URL: {url}
Title: {page_title}
Content sample: {text_content}

Determine if this website:
1. Publishes Brazilian mileage program content
2. Reports transfer bonus promotions (bônus de transferência)
3. Covers programs like Smiles, Azul, LATAM, Livelo, etc.
4. Would be valuable for tracking bonus alerts

Respond with JSON:
{{
    "is_relevant": true/false,
    "confidence": 0.0-1.0,
    "reason": "explanation",
    "detected_programs": ["program1", "program2"],
    "content_quality": "high/medium/low"
}}""",
                    },
                ],
                temperature=0.1,
                max_tokens=400,
            )

            # Parse AI response
            content = ai_response.choices[0].message.content
            if content:
                try:
                    result = cast(dict[str, Any], json.loads(content))
                    logger.info(f"AI validation for {url}: {result}")
                    return result
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse AI response for {url}")
                    return self._basic_validate_source(url)
            return self._basic_validate_source(url)

        except Exception as e:
            logger.error(f"AI validation failed for {url}: {e}")
            return self._basic_validate_source(url)

    def _basic_validate_source(self, url: str) -> dict[str, Any]:
        """Basic validation fallback"""
        domain = url.lower()
        keywords = [
            "milhas",
            "miles",
            "pontos",
            "smiles",
            "azul",
            "latam",
            "gol",
            "livelo",
        ]

        is_relevant = any(keyword in domain for keyword in keywords)

        return {
            "is_relevant": is_relevant,
            "confidence": 0.6 if is_relevant else 0.2,
            "reason": f"Domain-based detection: {domain}",
            "detected_programs": [],
            "content_quality": "unknown",
        }

    def discover_and_add_sources(self) -> list[str]:
        """Main method to discover and add new sources"""
        logger.info("🧠 Starting AI-powered source discovery...")

        # Generate intelligent search queries
        queries = self.generate_search_queries()
        logger.info(f"Using queries: {queries}")

        # Search multiple engines
        candidate_urls = self.search_multiple_engines(queries)
        logger.info(f"Found {len(candidate_urls)} candidate URLs")

        # Filter out existing sources
        existing_sources = set(self.store.all())
        new_candidates = [url for url in candidate_urls if url not in existing_sources]
        logger.info(f"Filtering to {len(new_candidates)} new candidates")

        # AI validation and addition
        added_sources: list[str] = []
        for url in new_candidates[:10]:  # Limit to 10 to avoid rate limits
            try:
                validation = self.ai_validate_source(url)

                if (
                    validation.get("is_relevant")
                    and validation.get("confidence", 0) > 0.7
                ):
                    if self.store.add(url):
                        added_sources.append(url)
                        logger.info(f"✅ Added high-quality source: {url}")
                    else:
                        logger.warning(f"❌ Failed to add source: {url}")
                else:
                    logger.info(f"⏭️ Skipped low-confidence source: {url}")

            except Exception as e:
                logger.error(f"Error processing {url}: {e}")

        # Send notification
        if added_sources:
            try:
                message = (
                    f"🧠 AI discovered {len(added_sources)} high-quality mileage sources:\n"
                    + "\n".join(added_sources)
                )
                send_telegram(message)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

        logger.info(f"AI source discovery complete: {len(added_sources)} sources added")
        return added_sources


def ai_update_sources() -> list[str]:
    """Main function for AI-powered source updates"""
    discovery = AISourceDiscovery()
    return discovery.discover_and_add_sources()


if __name__ == "__main__":
    # Test the AI discovery
    logging.basicConfig(level=logging.INFO)
    added = ai_update_sources()
    print(f"Added {len(added)} sources: {added}")
