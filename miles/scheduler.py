from __future__ import annotations

import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from bonus_alert_bot import run_scan


def setup_scheduler() -> None:
    scheduler = AsyncIOScheduler(event_loop=asyncio.get_running_loop())
    scheduler.add_job(run_scan, "cron", hour=15, minute=0)
    scheduler.add_job(run_scan, "cron", hour=23, minute=0)
    scheduler.start()

if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run_scan))

