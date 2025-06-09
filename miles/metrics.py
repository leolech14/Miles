"""Prometheus metrics for Miles bot monitoring."""

from __future__ import annotations

import time
from contextlib import contextmanager
from typing import Iterator

import prometheus_client
from prometheus_client import Counter, Histogram, Gauge, Info


# Bot operation metrics
promo_scrape_duration = Histogram(
    "promo_scrape_duration_seconds",
    "Time spent scraping promotions from sources",
    ["plugin", "source"],
)

promo_scrape_total = Counter(
    "promo_scrape_total",
    "Total number of promotion scrape attempts",
    ["plugin", "source", "status"],  # status: success, error, timeout
)

promos_found_total = Counter(
    "promos_found_total",
    "Total number of promotions found",
    ["plugin", "source", "program"],
)

# Telegram bot metrics
telegram_commands_total = Counter(
    "telegram_commands_total",
    "Total number of Telegram commands processed",
    ["command", "status"],  # status: success, error
)

telegram_messages_sent_total = Counter(
    "telegram_messages_sent_total",
    "Total number of Telegram messages sent",
    ["type"],  # type can be notification, response, error
)

# AI/OpenAI metrics
llm_requests_total = Counter(
    "llm_requests_total",
    "Total number of LLM API requests",
    ["model", "endpoint", "status"],
)

llm_tokens_total = Counter(
    "llm_tokens_total",
    "Total number of LLM tokens used",
    ["model", "type"],  # type can be input, output
)

llm_response_duration = Histogram(
    "llm_response_duration_seconds",
    "Time spent waiting for LLM responses",
    ["model", "endpoint"],
)

# Plugin system metrics
plugin_load_duration = Histogram(
    "plugin_load_duration_seconds",
    "Time spent loading plugins",
    ["plugin"],
)

plugin_execution_duration = Histogram(
    "plugin_execution_duration_seconds",
    "Time spent executing plugin methods",
    ["plugin", "method"],
)

plugin_errors_total = Counter(
    "plugin_errors_total",
    "Total number of plugin execution errors",
    ["plugin", "error_type"],
)

# Redis/Storage metrics
redis_operations_total = Counter(
    "redis_operations_total",
    "Total number of Redis operations",
    ["operation", "status"],  # operation: get, set, delete, etc.
)

redis_response_duration = Histogram(
    "redis_response_duration_seconds",
    "Time spent on Redis operations",
    ["operation"],
)

# Source monitoring metrics
sources_active = Gauge(
    "sources_active_total",
    "Number of currently active sources being monitored",
)

sources_response_duration = Histogram(
    "sources_response_duration_seconds",
    "Time spent fetching content from sources",
    ["source_domain"],
)

sources_response_size = Histogram(
    "sources_response_size_bytes",
    "Size of response content from sources",
    ["source_domain"],
)

# System health metrics
scheduler_jobs_active = Gauge(
    "scheduler_jobs_active",
    "Number of active scheduled jobs",
)

memory_usage_bytes = Gauge(
    "memory_usage_bytes",
    "Current memory usage in bytes",
)

# Bot info
bot_info = Info(
    "miles_bot_info",
    "Information about the Miles bot instance",
)

# Initialize bot info
try:
    import miles
    from miles.plugin_loader import discover_plugins
    import os

    plugins_count = len(discover_plugins())
    bot_info.info(
        {
            "version": getattr(miles, "__version__", "unknown"),
            "python_version": f"{__import__('sys').version_info.major}.{__import__('sys').version_info.minor}",
            "plugins_available": str(plugins_count),
            "redis_configured": (
                "true" if os.getenv("REDIS_URL", "not_set") != "not_set" else "false"
            ),
            "openai_configured": (
                "true"
                if os.getenv("OPENAI_API_KEY", "not_set") != "not_set"
                else "false"
            ),
        }
    )
except Exception:
    # Fallback if imports fail
    bot_info.info({"status": "initialization_error"})


# Context managers for timing operations
@contextmanager
def time_operation(histogram: Histogram, *labels: str) -> Iterator[None]:
    """Context manager to time operations and record to histogram."""
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        histogram.labels(*labels).observe(duration)


@contextmanager
def count_operation(
    counter: Counter, *labels: str, status: str = "success"
) -> Iterator[None]:
    """Context manager to count operations and handle errors."""
    try:
        yield
        counter.labels(*labels, status).inc()
    except Exception:
        counter.labels(*labels, "error").inc()
        raise


# Utility functions
def update_active_sources_count(count: int) -> None:
    """Update the active sources gauge."""
    sources_active.set(count)


def record_memory_usage() -> None:
    """Record current memory usage."""
    try:
        import psutil
        import os

        process = psutil.Process(os.getpid())
        memory_usage_bytes.set(process.memory_info().rss)
    except ImportError:
        # psutil not available, skip memory monitoring
        pass


def record_scheduler_jobs(count: int) -> None:
    """Record number of active scheduler jobs."""
    scheduler_jobs_active.set(count)


def get_metrics_registry() -> prometheus_client.CollectorRegistry:
    """Get the metrics registry for exposing metrics."""
    return prometheus_client.REGISTRY
