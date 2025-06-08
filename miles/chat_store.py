from __future__ import annotations

from datetime import datetime, timedelta  # noqa: F401
import json
import os
from typing import cast, Optional
import redis
import sys


class ChatMemory:
    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r: Optional[redis.Redis[str]] = None
        if url == "not_set":
            print(
                "[chat_store] Redis URL not configured, chat history will not persist",
                file=sys.stderr,
            )
        else:
            try:
                redis_client = redis.Redis.from_url(url, decode_responses=True)
                # Test connection
                redis_client.ping()
                self.r = redis_client
            except Exception as e:
                print(f"[chat_store] Redis connection failed: {e}", file=sys.stderr)
        self.ttl = int(os.getenv("CHAT_TTL_MINUTES", "30"))

    def _key(self, user_id: int) -> str:
        return f"chat:{user_id}"

    def get(self, user_id: int) -> list[dict[str, str]]:
        if not self.r:
            return []
        raw = self.r.get(self._key(user_id))
        if raw:
            return cast(list[dict[str, str]], json.loads(str(raw)))
        return []

    def save(self, user_id: int, messages: list[dict[str, str]]) -> None:
        if not self.r:
            return
        self.r.set(self._key(user_id), json.dumps(messages), ex=self.ttl * 60)

    def clear(self, user_id: int) -> None:
        if not self.r:
            return
        self.r.delete(self._key(user_id))

    def _pref_key(self, user_id: int) -> str:
        return f"prefs:{user_id}"

    def get_user_preference(self, user_id: int, key: str) -> Optional[str]:
        if not self.r:
            return None
        prefs_raw = self.r.get(self._pref_key(user_id))
        if prefs_raw:
            prefs = json.loads(str(prefs_raw))
            return str(prefs.get(key)) if prefs.get(key) is not None else None
        return None

    def set_user_preference(self, user_id: int, key: str, value: str) -> None:
        if not self.r:
            return
        prefs_raw = self.r.get(self._pref_key(user_id))
        prefs = json.loads(str(prefs_raw)) if prefs_raw else {}
        prefs[key] = value
        self.r.set(self._pref_key(user_id), json.dumps(prefs), ex=86400 * 30)  # 30 days

    def get_all_user_preferences(self, user_id: int) -> dict[str, str]:
        if not self.r:
            return {}
        prefs_raw = self.r.get(self._pref_key(user_id))
        if prefs_raw:
            prefs = json.loads(str(prefs_raw))
            return {k: str(v) for k, v in prefs.items()}
        return {}
