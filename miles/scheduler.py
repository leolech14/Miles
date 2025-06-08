from __future__ import annotations

import asyncio
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo

from miles.bonus_alert_bot import run_scan
from miles.source_search import update_sources
from miles.ai_source_discovery import ai_update_sources
from miles.schedule_config import ScheduleConfig


TIMEZONE = ZoneInfo("America/Sao_Paulo")
_scheduler: Optional[AsyncIOScheduler] = None


def setup_scheduler() -> None:
    global _scheduler
    loop = asyncio.get_running_loop()
    _scheduler = AsyncIOScheduler(event_loop=loop, timezone=TIMEZONE)

    # Load configuration
    config = ScheduleConfig().get_config()

    # Add jobs based on configuration - use AI discovery
    _scheduler.add_job(
        ai_update_sources,
        "cron",
        hour=config["update_hour"],
        minute=0,
        id="ai_update_sources",
    )

    scan_hours = config["scan_hours"]
    if isinstance(scan_hours, list):
        for hour in scan_hours:
            _scheduler.add_job(run_scan, "cron", hour=hour, minute=0, id=f"scan_{hour}")

    _scheduler.start()


def update_schedule() -> bool:
    """Update the scheduler with new configuration"""
    global _scheduler
    if not _scheduler:
        return False

    config = ScheduleConfig().get_config()

    try:
        # Remove existing jobs
        for job in _scheduler.get_jobs():
            _scheduler.remove_job(job.id)

        # Add new jobs
        _scheduler.add_job(
            update_sources,
            "cron",
            hour=config["update_hour"],
            minute=0,
            id="update_sources",
        )

        scan_hours = config["scan_hours"]
        if isinstance(scan_hours, list):
            for hour in scan_hours:
                _scheduler.add_job(
                    run_scan, "cron", hour=hour, minute=0, id=f"scan_{hour}"
                )

        return True
    except Exception:
        return False


def get_current_schedule() -> Dict[str, Any]:
    """Get current schedule configuration"""
    return ScheduleConfig().get_config()


if __name__ == "__main__":
    asyncio.run(asyncio.to_thread(run_scan))
