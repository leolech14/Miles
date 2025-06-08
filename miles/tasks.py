from typing import Protocol
import logging

logger = logging.getLogger(__name__)


class Promotion(Protocol):
    """Protocol for promotion objects"""

    canonical_id: str


class DeduplicatorProtocol(Protocol):
    """Protocol for deduplication"""

    def seen(self, promo: Promotion) -> bool: ...


def deduper() -> DeduplicatorProtocol:
    """Create a deduplicator instance"""

    class D:
        @staticmethod
        def seen(promo: Promotion) -> bool:
            return False

    return D()


deduper_instance: DeduplicatorProtocol = deduper()


async def save_promo(promo: Promotion, duplicate: bool = False) -> None:
    """Save promotion to storage"""
    pass


class Telegram:
    """Telegram notification service"""

    async def send_promotion(self, promo: Promotion) -> None:
        """Send promotion notification"""
        pass


telegram = Telegram()


async def _process(promo: Promotion) -> None:
    """Process a promotion through the pipeline"""
    is_dup = deduper_instance.seen(promo)
    await save_promo(promo, duplicate=is_dup)
    if is_dup:
        logger.debug("Duplicate skipped: %s", promo.canonical_id)
        return
    await telegram.send_promotion(promo)
