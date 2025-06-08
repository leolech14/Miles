"""Configuration module for Miles bot."""
from typing import Any
from pydantic import Field

try:
    from pydantic_settings import BaseSettings
except ImportError:
    from pydantic import BaseSettings  # type: ignore[attr-defined]


class Settings(BaseSettings):
    """Application settings."""

    redis_url: str = Field("redis://localhost:6379/0", env="REDIS_URL")
    database_url: str = Field(..., env="DATABASE_URL")
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    telegram_bot_token: str = Field(..., env="TELEGRAM_BOT_TOKEN")

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
