"""
Enhanced Configuration for Natural Language Miles Bot

Optimized settings for conversational AI experience.
"""

import os
from typing import Any


class NaturalLanguageConfig:
    """Configuration optimized for natural language interactions."""

    def __init__(self, **kwargs: Any) -> None:
        # Core settings
        self.redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.database_url = os.getenv("DATABASE_URL", "sqlite:///miles.db")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "not_set")
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "not_set")
        self.telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        # Natural language specific settings
        self.default_model = os.getenv(
            "OPENAI_MODEL", "gpt-4o"
        )  # Better for function calling
        self.default_temperature = float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
        self.default_max_tokens = int(
            os.getenv("OPENAI_MAX_TOKENS", "2000")
        )  # Longer responses
        self.conversation_timeout = int(
            os.getenv("CONVERSATION_TIMEOUT", "1800")
        )  # 30 minutes

        # Enhanced features
        self.enable_proactive_suggestions = (
            os.getenv("ENABLE_PROACTIVE_SUGGESTIONS", "true").lower() == "true"
        )
        self.enable_performance_insights = (
            os.getenv("ENABLE_PERFORMANCE_INSIGHTS", "true").lower() == "true"
        )
        self.enable_multimodal = (
            os.getenv("ENABLE_MULTIMODAL", "true").lower() == "true"
        )
        self.enable_function_explanations = (
            os.getenv("ENABLE_FUNCTION_EXPLANATIONS", "true").lower() == "true"
        )

        # Rate limiting (more generous for natural conversation)
        self.rate_limit_messages_per_minute = int(
            os.getenv("RATE_LIMIT_MESSAGES", "30")
        )
        self.rate_limit_functions_per_minute = int(
            os.getenv("RATE_LIMIT_FUNCTIONS", "20")
        )
        self.rate_limit_openai_per_minute = int(os.getenv("RATE_LIMIT_OPENAI", "60"))

        # Monitoring and health
        self.health_check_port = int(os.getenv("HEALTH_CHECK_PORT", "8080"))
        self.metrics_enabled = os.getenv("METRICS_ENABLED", "true").lower() == "true"
        self.log_webhook_url = os.getenv("LOG_WEBHOOK_URL", "")

        # Bot behavior
        self.min_bonus = int(os.getenv("MIN_BONUS", "80"))
        self.sources_path = os.getenv("SOURCES_PATH", "sources.yaml")
        self.plugins_enabled = os.getenv("PLUGINS_ENABLED", "")  # Empty = all enabled

        # Override with any provided kwargs
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict[str, Any]:
        """Convert config to dictionary."""
        return {
            attr: getattr(self, attr)
            for attr in dir(self)
            if not attr.startswith("_") and not callable(getattr(self, attr))
        }

    def validate(self) -> dict[str, str]:
        """Validate configuration and return any errors."""
        errors = {}

        if self.openai_api_key in {"not_set", "dummy", "placeholder", ""}:
            errors["openai_api_key"] = (
                "OpenAI API key is required for natural language features"
            )

        if self.telegram_bot_token in {"not_set", "dummy", "placeholder", ""}:
            errors["telegram_bot_token"] = (
                "Telegram bot token is required"  # Expected error message
            )

        if not self.telegram_chat_id:
            errors["telegram_chat_id"] = "Telegram chat ID is required"

        if self.default_temperature < 0 or self.default_temperature > 2:
            errors["default_temperature"] = "Temperature must be between 0 and 2"

        if self.default_max_tokens < 100 or self.default_max_tokens > 4096:
            errors["default_max_tokens"] = "Max tokens must be between 100 and 4096"

        return errors

    def get_openai_config(
        self, user_preferences: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Get OpenAI configuration with user preferences."""
        config = {
            "model": self.default_model,
            "temperature": self.default_temperature,
            "max_tokens": self.default_max_tokens,
        }

        if user_preferences:
            config.update(
                {
                    "model": user_preferences.get("model", config["model"]),
                    "temperature": float(
                        user_preferences.get("temperature", config["temperature"])
                    ),
                    "max_tokens": int(
                        user_preferences.get("max_tokens", config["max_tokens"])
                    ),
                }
            )

        return config


def get_natural_language_config() -> NaturalLanguageConfig:
    """Get the natural language configuration."""
    return NaturalLanguageConfig()


# Example environment file for reference
ENV_EXAMPLE = """
# Natural Language Miles Bot Configuration

# Required
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
OPENAI_API_KEY=sk-proj-your_openai_key_here

# Optional - Database
REDIS_URL=redis://localhost:6379/0
DATABASE_URL=postgresql://user:pass@localhost/miles

# Optional - AI Configuration
OPENAI_MODEL=gpt-4o
OPENAI_TEMPERATURE=0.7
OPENAI_MAX_TOKENS=2000
CONVERSATION_TIMEOUT=1800

# Optional - Features
ENABLE_PROACTIVE_SUGGESTIONS=true
ENABLE_PERFORMANCE_INSIGHTS=true
ENABLE_MULTIMODAL=true
ENABLE_FUNCTION_EXPLANATIONS=true

# Optional - Rate Limiting
RATE_LIMIT_MESSAGES=30
RATE_LIMIT_FUNCTIONS=20
RATE_LIMIT_OPENAI=60

# Optional - Monitoring
HEALTH_CHECK_PORT=8080
METRICS_ENABLED=true
LOG_WEBHOOK_URL=https://your-webhook-url.com

# Optional - Bot Behavior
MIN_BONUS=80
SOURCES_PATH=sources.yaml
PLUGINS_ENABLED=
"""

if __name__ == "__main__":
    # Print example configuration
    print("Natural Language Miles Bot Configuration Example:")
    print(ENV_EXAMPLE)

    # Validate current configuration
    config = get_natural_language_config()
    errors = config.validate()

    if errors:
        print("Configuration Errors:")
        for key, error in errors.items():
            print(f"  {key}: {error}")
    else:
        print("✅ Configuration is valid!")
