"""
Light-weight public contract that every plug-in must satisfy.

A *plug-in* is a Python object (usually a class instance) that exposes:
    • `name`        - unique, kebab-case identifier
    • `schedule`    - cron string or APScheduler alias ("@hourly")
    • `categories`  - arbitrary labels e.g. ["bonus"] / ["award_search"]
    • `scrape()`    - coroutine or function returning a list[Promo]

The core app discovers plug-ins through `importlib.metadata.entry_points`
(group ``milesbot_plugins``) and schedules their `scrape` method.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol, TypedDict


class Promo(TypedDict, total=False):
    program: str
    bonus_pct: int
    start_dt: datetime | None
    end_dt: datetime | None
    url: str
    title: str
    source: str  # plug-in ID


class Plugin(Protocol):
    name: str
    schedule: str
    categories: list[str]

    def scrape(self, since: datetime) -> list[Promo]: ...
