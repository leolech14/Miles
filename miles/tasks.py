from typing import Any
import logging

logger = logging.getLogger(__name__)

# Dummy class and functions for illustration; replace with actual implementations
class Promotion:
    canonical_id: str

def deduper():
    class D:
        @staticmethod
        def seen(promo):
            return False
    return D()
deduper = deduper()

async def save_promo(promo: 'Promotion', duplicate: bool = False):
    pass

class Telegram:
    async def send_promotion(self, promo: 'Promotion'):
        pass

telegram = Telegram()

async def _process(promo: 'Promotion') -> None:
    is_dup = deduper.seen(promo)
    await save_promo(promo, duplicate=is_dup)
    if is_dup:
        logger.debug("Duplicate skipped: %s", promo.canonical_id)
        return
    await telegram.send_promotion(promo)