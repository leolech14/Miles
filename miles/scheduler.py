from __future__ import annotations

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo

from miles.bonus_alert_bot import run_scan
from miles.source_search import update_sources


TIMEZONE = ZoneInfo("America/Sao_Paulo")


def setup_scheduler() -> None:
    loop = asyncio.get_running_loop()
    scheduler = AsyncIOScheduler(event_loop=loop, timezone=TIMEZONE)
    scheduler.add_job(update_sources, "cron", hour=6, minute=0)
    scheduler.add_job(run_scan, "cron", hour=9, minute=0)
    scheduler.add_job(run_scan, "cron", hour=18, minute=0)
    scheduler.start()


if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run_scan))
