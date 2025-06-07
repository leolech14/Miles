from __future__ import annotations

from datetime import datetime, timedelta  # noqa: F401
import json
import os
from typing import cast
import redis


class ChatMemory:
    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.Redis.from_url(url, decode_responses=True)
        self.ttl = int(os.getenv("CHAT_TTL_MINUTES", "30"))

    def _key(self, user_id: int) -> str:
        return f"chat:{user_id}"

    def get(self, user_id: int) -> list[dict[str, str]]:
        raw = self.r.get(self._key(user_id))
        return cast(list[dict[str, str]], json.loads(raw)) if raw else []

    def save(self, user_id: int, messages: list[dict[str, str]]) -> None:
        self.r.set(self._key(user_id), json.dumps(messages), ex=self.ttl * 60)

    def clear(self, user_id: int) -> None:
        self.r.delete(self._key(user_id))
