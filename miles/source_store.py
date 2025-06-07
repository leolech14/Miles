import os
import redis
import yaml
import logging
from typing import List, Optional
import sys


class SourceStore:
    def __init__(self, yaml_path: str = "sources.yaml"):
        self.yaml_path = yaml_path
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r: Optional[redis.Redis[str]] = None
        if url == "not_set":
            print(
                "[source_store] Redis URL not configured, using file storage only",
                file=sys.stderr,
            )
        else:
            try:
                redis_client = redis.Redis.from_url(url, decode_responses=True)
                redis_client.ping()
                self.r = redis_client
            except Exception as e:
                print(f"[source_store] Redis connection failed: {e}", file=sys.stderr)
        if self.r and not self.r.exists("sources"):
            self._bootstrap_from_yaml()

    def _bootstrap_from_yaml(self) -> None:
        if not self.r:
            return
        try:
            with open(self.yaml_path) as f:
                data: List[str] = yaml.safe_load(f) or []
        except FileNotFoundError:
            data = []
        if data:
            self.r.sadd("sources", *data)

    def _flush_to_yaml(self) -> None:
        with open(self.yaml_path, "w") as f:
            yaml.safe_dump(sorted(self.all()), f)

    # public API ---------------------------------------------------------
    def all(self) -> List[str]:
        if not self.r:
            return []
        sources = self.r.smembers("sources")
        # smembers returns a set of strings when decode_responses=True
        return sorted(sources)

    def add(self, url: str) -> bool:
        if not self.r:
            print(
                "[source_store] Redis is not connected. Cannot add source.",
                file=sys.stderr,
            )
            return False
        if not url.startswith("http") or len(url) > 200:
            logging.warning("Rejected invalid URL: %s", url)
            return False
        if url in self.all():
            return False
        added: bool = (
            self.r.sadd("sources", url) == 1
        )  # Explicitly define `added` as bool
        if added:
            self.needs_flush = True
        return added

    def remove(self, token: str) -> str | None:
        if not self.r:
            print(
                "[source_store] Redis is not connected. Cannot remove source.",
                file=sys.stderr,
            )
            return None
        target = None
        if token.isdigit():
            try:
                target = self.all()[int(token) - 1]
            except IndexError:
                return None
        else:
            target = token
        removed = self.r.srem("sources", target)
        if removed:
            self._flush_to_yaml()
            return target
        return None
