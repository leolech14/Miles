from __future__ import annotations

import json
import os
import hashlib
from typing import Set

import redis


class SeenStore:
    def has(self, h: str) -> bool:
        raise NotImplementedError

    def add(self, h: str) -> None:
        raise NotImplementedError


class RedisSeenStore(SeenStore):
    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r = redis.Redis.from_url(url, decode_responses=True)

    def has(self, h: str) -> bool:
        return bool(self.r.sismember("seen_hashes", h))

    def add(self, h: str) -> None:
        self.r.sadd("seen_hashes", h)


class FileSeenStore(SeenStore):
    def __init__(self, path: str = "seen.json") -> None:
        self.path = path
        try:
            with open(path) as f:
                self._data: Set[str] = set(json.load(f))
        except FileNotFoundError:
            self._data = set()

    def has(self, h: str) -> bool:
        return h in self._data

    def add(self, h: str) -> None:
        self._data.add(h)
        with open(self.path, "w") as f:
            json.dump(list(self._data), f)


def get_store() -> SeenStore:
    try:
        return RedisSeenStore()
    except redis.ConnectionError:
        return FileSeenStore()
