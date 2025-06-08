"""Miles - Telegram Bonus Alert Bot for Brazilian Mileage Programs"""

from miles.logging_config import setup_logging
from miles.bonus_alert_bot import run_scan, main
from miles.source_store import SourceStore
from miles.ai_source_discovery import ai_update_sources

__version__ = "0.1.0"

# Set up logging once at package level
setup_logging()

__all__ = [
    "__version__",
    "run_scan",
    "main",
    "SourceStore",
    "ai_update_sources",
]
