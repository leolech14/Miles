import logging
import os
import sys

import redis
import yaml


class SourceStore:
    def __init__(self, yaml_path: str = "sources.yaml"):
        self.yaml_path = yaml_path
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r: redis.Redis[str] | None = None
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
                data: list[str] = yaml.safe_load(f) or []
        except FileNotFoundError:
            data = []
        if data:
            self.r.sadd("sources", *data)

    def _flush_to_yaml(self) -> None:
        with open(self.yaml_path, "w") as f:
            yaml.safe_dump(sorted(self.all()), f)

    # public API ---------------------------------------------------------
    def all(self) -> list[str]:
        if not self.r:
            # Fall back to reading from YAML file when Redis is not available
            try:
                with open(self.yaml_path) as f:
                    data: list[str] = yaml.safe_load(f) or []
                return sorted(data)
            except FileNotFoundError:
                return []
        try:
            from miles.metrics import (
                count_operation,
                redis_operations_total,
                redis_response_duration,
                time_operation,
            )

            with (
                time_operation(redis_response_duration, "smembers"),
                count_operation(redis_operations_total, "smembers"),
            ):
                sources = self.r.smembers("sources")
        except ImportError:
            # Metrics not available, run without instrumentation
            sources = self.r.smembers("sources")
        # smembers returns a set of strings when decode_responses=True
        return sorted(sources)

    def add(self, url: str) -> bool:
        if not url.startswith("http") or len(url) > 200:
            logging.warning("Rejected invalid URL: %s", url)
            return False
        if url in self.all():
            return False

        if not self.r:
            # Fall back to file storage when Redis is not available
            try:
                current_sources = self.all()
                current_sources.append(url)
                with open(self.yaml_path, "w") as f:
                    yaml.safe_dump(sorted(current_sources), f)
                return True
            except Exception as e:
                print(
                    f"[source_store] Failed to add source to file: {e}", file=sys.stderr
                )
                return False

        added: bool = (
            self.r.sadd("sources", url) == 1
        )  # Explicitly define `added` as bool
        if added:
            self._flush_to_yaml()
        return added

    def remove(self, token: str) -> str | None:
        # Determine target URL
        target = None
        all_sources = self.all()
        if token.isdigit():
            try:
                target = all_sources[int(token) - 1]
            except IndexError:
                return None
        else:
            target = token

        if target not in all_sources:
            return None

        if not self.r:
            # Fall back to file storage when Redis is not available
            try:
                updated_sources = [s for s in all_sources if s != target]
                with open(self.yaml_path, "w") as f:
                    yaml.safe_dump(sorted(updated_sources), f)
                return target
            except Exception as e:
                print(
                    f"[source_store] Failed to remove source from file: {e}",
                    file=sys.stderr,
                )
                return None

        removed = self.r.srem("sources", target)
        if removed:
            self._flush_to_yaml()
            return target
        return None
