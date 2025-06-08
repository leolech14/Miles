from __future__ import annotations

import asyncio
import logging
from typing import Dict, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo

from miles.logging_config import setup_logging
from miles.schedule_config import ScheduleConfig
from miles.source_search import update_sources
from miles.ai_source_discovery import ai_update_sources
from miles.bonus_alert_bot import run_scan

"""
AsyncIO-based cron scheduler.  Import `setup_scheduler()` during application
startup (e.g. `__main__.py`, FastAPI lifespan event, or a standalone script).
"""

setup_logging()
logger = logging.getLogger("miles.scheduler")

TIMEZONE = ZoneInfo("America/Sao_Paulo")
_scheduler: Optional[AsyncIOScheduler] = None


def setup_scheduler() -> None:
    global _scheduler
    loop = asyncio.get_running_loop()
    _scheduler = AsyncIOScheduler(event_loop=loop, timezone=TIMEZONE)

    cfg = ScheduleConfig().get_config()

    # Add jobs based on configuration - use AI discovery
    _scheduler.add_job(
        ai_update_sources,
        "cron",
        hour=cfg["update_hour"],
        minute=0,
        id="ai_update_sources",
    )

    # Main scan jobs – possibly multiple hours per day
    for hour in cfg["scan_hours"]:
        _scheduler.add_job(run_scan, "cron", hour=hour, minute=0, id=f"scan_{hour}")

    _scheduler.start()
    logger.info("Scheduler started with %s job(s)", len(_scheduler.get_jobs()))


def update_schedule() -> bool:
    """Hot-reload APScheduler with new configuration values."""
    global _scheduler
    if _scheduler is None:
        return False

    cfg = ScheduleConfig().get_config()
    try:
        # Remove existing jobs
        for job in _scheduler.get_jobs():
            _scheduler.remove_job(job.id)

        # Add new jobs
        _scheduler.add_job(
            update_sources,
            "cron",
            hour=cfg["update_hour"],
            minute=0,
            id="update_sources",
        )

        scan_hours = cfg["scan_hours"]
        if isinstance(scan_hours, list):
            for hour in scan_hours:
                _scheduler.add_job(
                    run_scan, "cron", hour=hour, minute=0, id=f"scan_{hour}"
                )

        return True
    except Exception:
        return False


def get_current_schedule() -> Dict[str, object]:
    """Get current schedule configuration"""
    return ScheduleConfig().get_config()


if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run_scan))
