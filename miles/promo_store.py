"""Promo storage and notification system."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import datetime, UTC
from typing import List, Set, Optional

import redis

from miles.plugin_api import Promo
from config import get_settings

logger = logging.getLogger("miles.promo_store")


class PromoStore:
    """Handles storage and deduplication of promotion objects."""

    def __init__(self) -> None:
        settings = get_settings()
        self._redis: Optional[redis.Redis[str]] = None
        try:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
            self._redis.ping()  # Test connection
            self._use_redis = True
        except Exception:
            logger.warning("Redis unavailable, using in-memory storage")
            self._redis = None
            self._use_redis = False
            self._memory_store: Set[str] = set()

    def add_promos(self, promos: List[Promo]) -> List[Promo]:
        """Add promos to store, returning only new ones."""
        new_promos = []

        for promo in promos:
            promo_hash = self._hash_promo(promo)

            if not self._is_seen(promo_hash):
                self._mark_seen(promo_hash)
                new_promos.append(promo)
                logger.info(
                    f"New promo: {promo.get('title', 'Untitled')} ({promo.get('bonus_pct', 0)}%)"
                )

        return new_promos

    def _hash_promo(self, promo: Promo) -> str:
        """Generate unique hash for promo deduplication."""
        # Use key fields that identify unique promotions
        key_data = {
            "program": promo.get("program", ""),
            "bonus_pct": promo.get("bonus_pct", 0),
            "url": promo.get("url", ""),
            "title": promo.get("title", "")[:100],  # Limit title length
        }

        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()

    def _is_seen(self, promo_hash: str) -> bool:
        """True if promo_id is already persisted."""
        if self._use_redis and self._redis:
            return bool(self._redis.sismember("miles:seen_promos", promo_hash))
        else:
            return promo_hash in self._memory_store

    def _mark_seen(self, promo_hash: str) -> None:
        """Mark promo as seen."""
        if self._use_redis and self._redis:
            # Store with 30-day expiry to prevent infinite growth
            self._redis.sadd("miles:seen_promos", promo_hash)
            self._redis.expire("miles:seen_promos", 30 * 24 * 3600)
        else:
            self._memory_store.add(promo_hash)

    def get_stats(self) -> dict[str, object]:
        """Get storage statistics."""
        if self._use_redis and self._redis:
            total_seen = self._redis.scard("miles:seen_promos")
            return {"backend": "redis", "total_seen": total_seen, "connected": True}
        else:
            return {
                "backend": "memory",
                "total_seen": len(self._memory_store),
                "connected": False,
            }


class PromoNotifier:
    """Handles notifications for new promotions."""

    def __init__(self) -> None:
        self.min_bonus = int(os.getenv("MIN_BONUS", "80"))

    def notify_promos(self, promos: List[Promo]) -> None:
        """Send notifications for qualifying promos."""
        qualifying_promos = self._filter_promos(promos)

        if not qualifying_promos:
            return

        for promo in qualifying_promos:
            self._send_notification(promo)

    def _filter_promos(self, promos: List[Promo]) -> List[Promo]:
        """Filter promos that meet notification criteria."""
        filtered = []

        for promo in promos:
            bonus_pct = promo.get("bonus_pct", 0)

            # Skip source discovery notifications (bonus_pct = 0)
            if bonus_pct == 0:
                continue

            # Check minimum bonus threshold
            if bonus_pct >= self.min_bonus:
                filtered.append(promo)

        return filtered

    def _send_notification(self, promo: Promo) -> None:
        """Send notification for a single promo."""
        try:
            from miles.bonus_alert_bot import send_telegram

            program = promo.get("program", "Unknown")
            bonus_pct = promo.get("bonus_pct", 0)
            title = promo.get("title", "Bonus promotion detected")
            url = promo.get("url", "")
            source = promo.get("source", "unknown")

            # Format notification message
            message = f"""🎯 <b>{program} - {bonus_pct}% Bonus!</b>

{title}

🔗 <a href="{url}">Ver promoção</a>
📊 Fonte: {source}
⏰ {datetime.now(UTC).strftime('%H:%M - %d/%m/%Y')}"""

            send_telegram(message)
            logger.info(f"Notification sent: {program} {bonus_pct}% bonus")

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")


# Global instances
_promo_store: Optional[PromoStore] = None
_promo_notifier: Optional[PromoNotifier] = None


def get_promo_store() -> PromoStore:
    """Get global promo store instance."""
    global _promo_store
    if _promo_store is None:
        _promo_store = PromoStore()
    return _promo_store


def get_promo_notifier() -> PromoNotifier:
    """Get global promo notifier instance."""
    global _promo_notifier
    if _promo_notifier is None:
        _promo_notifier = PromoNotifier()
    return _promo_notifier


def process_plugin_promos(promos: List[Promo]) -> None:
    """Process promos from plugins - deduplication and notification."""
    if not promos:
        return

    store = get_promo_store()
    notifier = get_promo_notifier()

    # Deduplicate and get only new promos
    new_promos = store.add_promos(promos)

    # Send notifications for qualifying promos
    if new_promos:
        notifier.notify_promos(new_promos)
        logger.info(f"Processed {len(new_promos)} new promos from {len(promos)} total")
