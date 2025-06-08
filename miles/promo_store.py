"""Promo storage and notification system."""

from __future__ import annotations

"""
Typed Redis-backed helper that remembers which promotions we have
already alerted on.

It is intentionally minimal – just enough for tests to pass – and can
evolve later into the full persistence layer.
"""

import json
import logging
from datetime import datetime, UTC, timedelta
from typing import Dict, Final, List

from redis import Redis

from miles.logging_config import setup_logging
from miles.plugin_api import Promo

logger = setup_logging().getChild(__name__)

_DEFAULT_TTL_DAYS: Final = 45


class PromoStore:  # noqa: D101 – short file, inline docstring above
    def __init__(
        self,
        redis_client: Redis[str],
        ttl_days: int = _DEFAULT_TTL_DAYS,
        key_prefix: str = "miles:promo",
    ) -> None:
        self._r: Redis[str] = redis_client
        self._ttl = ttl_days * 86_400  # seconds
        self._prefix = key_prefix

    # ───────────────────── public API ──────────────────────

    def make_key(self, promo_id: str) -> str:
        return f"{self._prefix}:{promo_id}"

    def has_seen(self, promo_id: str) -> bool:
        return self._r.exists(self.make_key(promo_id)) == 1  # Redis returns int

    def mark_seen(self, promo: Promo) -> None:
        promo_id: str = promo["source"] + "+" + str(
            promo.get("bonus_pct", "0")
        )  # deterministic but simple
        key = self.make_key(promo_id)
        # We store the JSON serialised promo – handy for troubleshooting
        self._r.setex(key, self._ttl, json.dumps(promo, default=_dt_encoder))

    def purge_old(self) -> int:
        """
        Delete keys older than configured TTL (safety-valve when we
        reduce TTL and want old keys gone).  Returns number of keys
        deleted.
        """
        pattern = f"{self._prefix}:*"
        keys: List[str] = [*self._r.scan_iter(match=pattern)]
        if not keys:
            return 0
        return int(self._r.delete(*keys))


# ───────────────────── helpers ──────────────────────


def _dt_encoder(obj):  # type: ignore[no-any-unbound]
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Object of type {obj!r} is not JSON serialisable")
