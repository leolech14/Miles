#!/usr/bin/env python3
"""
Keploy Test Server for Miles Bot

This creates a simple FastAPI server to test Miles bot functionality with Keploy.
We expose key bot functions as HTTP endpoints for testing.
"""

import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Setup environment variables at startup
if "TELEGRAM_BOT_TOKEN" not in os.environ:
    os.environ["TELEGRAM_BOT_TOKEN"] = "test_token_for_keploy"  # Test environment only
if "TELEGRAM_CHAT_ID" not in os.environ:
    os.environ["TELEGRAM_CHAT_ID"] = "test_chat_id"
if "OPENAI_API_KEY" not in os.environ:
    os.environ["OPENAI_API_KEY"] = "test_key_placeholder"
if "REDIS_URL" not in os.environ:
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"

from miles.plugin_loader import discover_plugins
from miles.promo_store import get_promo_store
from miles.source_store import SourceStore

app = FastAPI(
    title="Miles Bot API Test Server",
    description="Test server for Miles Telegram Bot with Keploy integration",
    version="1.0.0",
)


# Request/Response models
class ScanRequest(BaseModel):
    min_bonus: int = 80


class ScanResponse(BaseModel):
    alerts: list[dict[str, Any]]
    count: int
    status: str


class SourceRequest(BaseModel):
    url: str


class SourceResponse(BaseModel):
    sources: list[str]
    count: int


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "miles-bot-test", "version": "1.0.0"}


@app.get("/sources")
async def get_sources() -> SourceResponse:
    """Get all configured sources"""
    try:
        store = SourceStore()
        sources = store.all()
        return SourceResponse(sources=sources, count=len(sources))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/sources")
async def add_source(request: SourceRequest) -> dict[str, Any]:
    """Add a new source"""
    try:
        store = SourceStore()
        added = store.add(request.url)
        return {
            "url": request.url,
            "added": added,
            "status": "success" if added else "already_exists",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/scan")
async def manual_scan(request: ScanRequest) -> ScanResponse:
    """Run a manual scan for promotions"""
    try:
        # Simulate some test alerts
        test_alerts = [
            (
                request.min_bonus + 10,
                "test.com",
                f"Test {request.min_bonus + 10}% bonus",
            ),
            (
                request.min_bonus + 20,
                "example.com",
                f"Test {request.min_bonus + 20}% bonus",
            ),
        ]

        alerts_dict = [
            {"bonus_pct": alert[0], "source": alert[1], "description": alert[2]}
            for alert in test_alerts
        ]

        return ScanResponse(
            alerts=alerts_dict, count=len(alerts_dict), status="success"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/plugins")
async def get_plugins() -> dict[str, Any]:
    """Get all available plugins"""
    try:
        plugins = discover_plugins()
        plugin_info = {}

        for name, plugin in plugins.items():
            plugin_info[name] = {
                "name": plugin.name,
                "schedule": plugin.schedule,
                "categories": plugin.categories,
            }

        return {"plugins": plugin_info, "count": len(plugin_info), "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.get("/metrics")
async def get_metrics() -> dict[str, Any]:
    """Get bot metrics and stats"""
    try:
        # Get promo store stats
        promo_store = get_promo_store()
        store_stats = promo_store.get_stats()

        # Get source count
        source_store = SourceStore()
        source_count = len(source_store.all())

        return {
            "promo_store": store_stats,
            "source_count": source_count,
            "status": "healthy",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@app.post("/test-notification")
async def test_notification() -> dict[str, Any]:
    """Test the notification system"""
    try:
        # Create a test promo
        test_promo = {
            "program": "TEST_PROGRAM",
            "bonus_pct": 100,
            "title": "🧪 Keploy Test Promotion",
            "url": "https://test.example.com",
            "source": "keploy-test",
        }

        # Note: In real scenario this would send Telegram message
        # For testing, we just return success
        return {
            "promo": test_promo,
            "notification_sent": True,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


if __name__ == "__main__":
    print("🚀 Starting Miles Bot Test Server for Keploy...")
    print("📊 Available endpoints:")
    print("  GET  /         - Health check")
    print("  GET  /sources  - List sources")
    print("  POST /sources  - Add source")
    print("  POST /scan     - Run scan")
    print("  GET  /plugins  - List plugins")
    print("  GET  /metrics  - Bot metrics")
    print("  POST /test-notification - Test notifications")
    print("\n🔍 Starting server on http://localhost:8080")

    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")  # noqa: S104
