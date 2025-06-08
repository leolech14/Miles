"""Configuration module for Miles bot."""

import os
from typing import Any


class Settings:
    """Application settings."""

    def __init__(self, **kwargs: Any) -> None:
        # Set defaults first
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///test.db")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "not_set")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "not_set")

        # Override with any provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
