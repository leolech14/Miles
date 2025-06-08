"""Configuration module for Miles bot."""
import os
from typing import Any

try:
    from pydantic_settings import BaseSettings
    from pydantic import ConfigDict
except ImportError:
    from pydantic import BaseSettings  # type: ignore[attr-defined]
    ConfigDict = None


class Settings(BaseSettings):
    """Application settings."""
    
    redis_url: str = "redis://localhost:6379/0"
    database_url: str = "sqlite:///test.db"
    openai_api_key: str = "not_set"
    telegram_bot_token: str = "not_set"

    if ConfigDict:
        model_config = ConfigDict(env_file=".env")
    else:
        class Config:
            env_file = ".env"
    
    def __init__(self, **kwargs):
        # Set defaults first
        defaults = {
            'redis_url': os.getenv('REDIS_URL', "redis://localhost:6379/0"),
            'database_url': os.getenv('DATABASE_URL', "sqlite:///test.db"),
            'openai_api_key': os.getenv('OPENAI_API_KEY', "not_set"),
            'telegram_bot_token': os.getenv('TELEGRAM_BOT_TOKEN', "not_set"),
        }
        # Override with any provided kwargs
        defaults.update(kwargs)
        super().__init__(**defaults)


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
