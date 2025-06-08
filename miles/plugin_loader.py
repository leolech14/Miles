from __future__ import annotations

import logging
import os
from datetime import datetime, UTC
from importlib.metadata import entry_points
from typing import Dict, List, Any, Type

from apscheduler.schedulers.base import BaseScheduler

from miles.plugin_api import Plugin, Promo

logger = logging.getLogger("miles.plugin_loader")

_GROUP = "milesbot_plugins"
_ENV_VAR = "PLUGINS_ENABLED"  # comma-list or unset (= all)


def _enabled_set() -> set[str] | None:
    raw = os.getenv(_ENV_VAR)
    if not raw:
        return None
    return {part.strip() for part in raw.split(",") if part.strip()}


def discover_plugins() -> Dict[str, Plugin]:
    """Import & instantiate all enabled plug-ins."""
    enabled = _enabled_set()
    found: Dict[str, Plugin] = {}

    for ep in entry_points(group=_GROUP):
        if enabled is not None and ep.name not in enabled:
            continue
        try:
            plugin_cls: Type[Plugin] | None = ep.load()
            if plugin_cls is None:
                logger.error("Plugin class not defined for %s", ep.name)
                continue
            plugin: Plugin = plugin_cls()  # type: ignore[call-arg]
            found[plugin.name] = plugin
            logger.info("Loaded plug-in: %s", plugin.name)
        except Exception:  # noqa: BLE001
            logger.exception("Failed to load plug-in %s", ep.name)

    return found

def register_with_scheduler(scheduler: BaseScheduler) -> None:
    """
    Add every discovered plug-in to the running APScheduler instance.
    The `since` param passed to scrape() is *now minus one schedule run*,
    so a missed run does not create a gap.
    """
    now = datetime.now(tz=UTC)
    for plugin in discover_plugins().values():

        async def _runner(plg: Plugin = plugin) -> None:  # default-arg trick
            try:
                promos: List[Promo] = await _maybe_async(plg.scrape, now)
                logger.info("Plug-in %s produced %d promos", plg.name, len(promos))

                # Process promos through storage and notification system
                if promos:
                    from miles.promo_store import process_plugin_promos

                    process_plugin_promos(promos)

            except Exception:  # noqa: BLE001
                logger.exception("Plug-in %s execution failed", plg.name)

        scheduler.add_job(
            _runner, "cron", id=f"plugin_{plugin.name}", **_cron_kwargs(plugin.schedule)
        )


# ───────────────────────── helpers ──────────────────────────


async def _maybe_async(func: Any, *args: Any, **kwargs: Any) -> Any:
    res = func(*args, **kwargs)
    if hasattr(res, "__await__"):
        return await res
    return res


def _cron_kwargs(expr: str) -> dict[str, Any]:
    """Convert cron expression to APScheduler kwargs."""
    if expr.startswith("@"):
        # Handle aliases like @hourly, @daily, etc.
        alias = expr.lstrip("@")
        if alias == "hourly":
            return {"minute": "0"}
        elif alias == "daily":
            return {"hour": "0", "minute": "0"}
        elif alias == "weekly":
            return {"day_of_week": "0", "hour": "0", "minute": "0"}
        else:
            # Fallback for unknown aliases
            return {"hour": "*/1"}

    # Parse standard cron format: "min hour day month dow"
    parts = expr.split()
    return {
        "minute": parts[0] if len(parts) >= 1 else "*",
        "hour": parts[1] if len(parts) >= 2 else "*",
        "day": parts[2] if len(parts) >= 3 else "*",
        "month": parts[3] if len(parts) >= 4 else "*",
        "day_of_week": parts[4] if len(parts) >= 5 else "*",
    }
