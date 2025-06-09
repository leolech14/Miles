from __future__ import annotations

import contextlib
import json
import os
import sys
from datetime import datetime, timedelta  # noqa: F401
from pathlib import Path
from typing import cast

import redis


class ChatMemory:
    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r: redis.Redis[str] | None = None
        self.chat_dir = Path("chat_history")
        self.prefs_dir = Path("user_preferences")

        # Create directories for file fallback
        self.chat_dir.mkdir(exist_ok=True)
        self.prefs_dir.mkdir(exist_ok=True)

        if url == "not_set":
            print(
                "[chat_store] Redis URL not configured, using file storage fallback",
                file=sys.stderr,
            )
        else:
            try:
                redis_client = redis.Redis.from_url(url, decode_responses=True)
                # Test connection
                redis_client.ping()
                self.r = redis_client
                print("[chat_store] Redis connected successfully", file=sys.stderr)
            except Exception as e:
                print(f"[chat_store] Redis connection failed: {e}", file=sys.stderr)
                print("[chat_store] Using file storage fallback", file=sys.stderr)
        self.ttl = int(os.getenv("CHAT_TTL_MINUTES", "30"))

    def _key(self, user_id: int) -> str:
        return f"chat:{user_id}"

    def get(self, user_id: int) -> list[dict[str, str]]:
        if self.r:
            # Try Redis first
            raw = self.r.get(self._key(user_id))
            if raw:
                return cast(list[dict[str, str]], json.loads(str(raw)))
            return []
        else:
            # Fallback to file storage
            chat_file = self.chat_dir / f"{user_id}.json"
            if chat_file.exists():
                try:
                    with open(chat_file) as f:
                        data = json.load(f)
                        return cast(list[dict[str, str]], data)
                except (OSError, json.JSONDecodeError):
                    return []
            return []

    def save(self, user_id: int, messages: list[dict[str, str]]) -> None:
        if self.r:
            # Save to Redis
            self.r.set(self._key(user_id), json.dumps(messages), ex=self.ttl * 60)
        else:
            # Fallback to file storage
            chat_file = self.chat_dir / f"{user_id}.json"
            try:
                with open(chat_file, "w") as f:
                    json.dump(messages, f)
            except OSError:
                pass  # Silent fail for file write issues

    def clear(self, user_id: int) -> None:
        if self.r:
            # Clear from Redis
            self.r.delete(self._key(user_id))
        else:
            # Clear from file storage
            chat_file = self.chat_dir / f"{user_id}.json"
            if chat_file.exists():
                with contextlib.suppress(OSError):
                    chat_file.unlink()

    def _pref_key(self, user_id: int) -> str:
        return f"prefs:{user_id}"

    def get_user_preference(self, user_id: int, key: str) -> str | None:
        if self.r:
            # Try Redis first
            prefs_raw = self.r.get(self._pref_key(user_id))
            if prefs_raw:
                prefs = json.loads(str(prefs_raw))
                return str(prefs.get(key)) if prefs.get(key) is not None else None
            return None
        else:
            # Fallback to file storage
            prefs_file = self.prefs_dir / f"{user_id}.json"
            if prefs_file.exists():
                try:
                    with open(prefs_file) as f:
                        prefs = json.load(f)
                        return (
                            str(prefs.get(key)) if prefs.get(key) is not None else None
                        )
                except (OSError, json.JSONDecodeError):
                    return None
            return None

    def set_user_preference(self, user_id: int, key: str, value: str) -> None:
        if self.r:
            # Save to Redis
            prefs_raw = self.r.get(self._pref_key(user_id))
            prefs = json.loads(str(prefs_raw)) if prefs_raw else {}
            prefs[key] = value
            self.r.set(
                self._pref_key(user_id), json.dumps(prefs), ex=86400 * 30
            )  # 30 days
        else:
            # Fallback to file storage
            prefs_file = self.prefs_dir / f"{user_id}.json"
            try:
                # Load existing preferences
                if prefs_file.exists():
                    with open(prefs_file) as f:
                        prefs = json.load(f)
                else:
                    prefs = {}

                # Update and save
                prefs[key] = value
                with open(prefs_file, "w") as f:
                    json.dump(prefs, f)
            except (OSError, json.JSONDecodeError):
                pass  # Silent fail for file operations

    def get_all_user_preferences(self, user_id: int) -> dict[str, str]:
        if self.r:
            # Try Redis first
            prefs_raw = self.r.get(self._pref_key(user_id))
            if prefs_raw:
                prefs = json.loads(str(prefs_raw))
                return {k: str(v) for k, v in prefs.items()}
            return {}
        else:
            # Fallback to file storage
            prefs_file = self.prefs_dir / f"{user_id}.json"
            if prefs_file.exists():
                try:
                    with open(prefs_file) as f:
                        prefs = json.load(f)
                        return {k: str(v) for k, v in prefs.items()}
                except (OSError, json.JSONDecodeError):
                    return {}
            return {}
