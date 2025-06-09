"""
Function Registry for Natural Language Miles Bot

Defines all bot operations as OpenAI function calling schemas.
This replaces the command-based system with natural language understanding.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import miles.bonus_alert_bot as bot
from miles.chat_store import ChatMemory
from miles.plugin_loader import discover_plugins
from miles.schedule_config import ScheduleConfig
from miles.source_store import SourceStore


class FunctionRegistry:
    """Registry of all bot functions available to OpenAI."""

    def __init__(self) -> None:
        self.store = SourceStore()
        self.memory = ChatMemory()
        self.schedule_config = ScheduleConfig()

    def get_function_definitions(self) -> list[dict[str, Any]]:
        """Get all function definitions for OpenAI function calling."""
        return [
            {
                "name": "scan_for_promotions",
                "description": "Scan all sources for mileage transfer bonus promotions. Use this when user asks about current bonuses, deals, or wants to check for promotions.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "min_bonus": {
                            "type": "integer",
                            "description": "Minimum bonus percentage to look for (default 80)",
                            "default": 80,
                        }
                    },
                },
            },
            {
                "name": "list_sources",
                "description": "List all monitored sources. Use when user asks about sources, what sites are monitored, or wants to see the source list.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_stats": {
                            "type": "boolean",
                            "description": "Include source statistics and performance data",
                            "default": False,
                        }
                    },
                },
            },
            {
                "name": "add_source",
                "description": "Add a new source URL to monitor. Use when user provides a URL or asks to add a new mileage site.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The URL to add for monitoring",
                        },
                        "validate": {
                            "type": "boolean",
                            "description": "Whether to validate the URL before adding",
                            "default": True,
                        },
                    },
                    "required": ["url"],
                },
            },
            {
                "name": "remove_source",
                "description": "Remove a source from monitoring. Use when user wants to stop monitoring a specific site.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "identifier": {
                            "type": "string",
                            "description": "URL or index number of source to remove",
                        }
                    },
                    "required": ["identifier"],
                },
            },
            {
                "name": "discover_new_sources",
                "description": "Use AI to discover new mileage sources automatically. Use when user asks to find new sources or wants to expand monitoring.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "search_terms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Specific search terms or programs to focus on",
                            "default": ["milhas", "pontos", "transfer", "bonus"],
                        }
                    },
                },
            },
            {
                "name": "get_schedule",
                "description": "Get current scanning and update schedule. Use when user asks about timing, schedule, or when scans happen.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "set_scan_times",
                "description": "Set the times when promotion scans should run. Use when user wants to change scan timing.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hours": {
                            "type": "array",
                            "items": {"type": "integer", "minimum": 0, "maximum": 23},
                            "description": "Hours of day to run scans (24-hour format, São Paulo time)",
                        }
                    },
                    "required": ["hours"],
                },
            },
            {
                "name": "set_update_time",
                "description": "Set the time when source discovery/updates should run. Use when user wants to change when new sources are discovered.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "hour": {
                            "type": "integer",
                            "minimum": 0,
                            "maximum": 23,
                            "description": "Hour of day to run updates (24-hour format, São Paulo time)",
                        }
                    },
                    "required": ["hour"],
                },
            },
            {
                "name": "get_bot_status",
                "description": "Get comprehensive bot status including configuration, health, and performance. Use when user asks about bot status, settings, or diagnostics.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "manage_plugins",
                "description": "List, test, or get information about plugins. Use when user asks about plugins or wants to manage the plugin system.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "action": {
                            "type": "string",
                            "enum": ["list", "test", "info"],
                            "description": "Action to perform with plugins",
                        },
                        "plugin_name": {
                            "type": "string",
                            "description": "Name of specific plugin (for test/info actions)",
                        },
                    },
                    "required": ["action"],
                },
            },
            {
                "name": "export_sources",
                "description": "Export all sources as a text list. Use when user wants to backup or share their source list.",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "import_sources",
                "description": "Import sources from a list of URLs. Use when user provides multiple URLs to add.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "urls": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of URLs to import",
                        }
                    },
                    "required": ["urls"],
                },
            },
            {
                "name": "analyze_performance",
                "description": "Analyze bot performance and provide optimization suggestions. Use when user asks about performance, optimization, or wants insights.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "include_recommendations": {
                            "type": "boolean",
                            "description": "Include AI-powered optimization recommendations",
                            "default": True,
                        }
                    },
                },
            },
        ]

    def execute_function(
        self, function_name: str, arguments: dict[str, Any]
    ) -> dict[str, Any]:
        """Execute a function and return the result."""
        try:
            if function_name == "scan_for_promotions":
                return self._scan_for_promotions(**arguments)
            elif function_name == "list_sources":
                return self._list_sources(**arguments)
            elif function_name == "add_source":
                return self._add_source(**arguments)
            elif function_name == "remove_source":
                return self._remove_source(**arguments)
            elif function_name == "discover_new_sources":
                return self._discover_new_sources(**arguments)
            elif function_name == "get_schedule":
                return self._get_schedule()
            elif function_name == "set_scan_times":
                return self._set_scan_times(**arguments)
            elif function_name == "set_update_time":
                return self._set_update_time(**arguments)
            elif function_name == "get_bot_status":
                return self._get_bot_status()
            elif function_name == "manage_plugins":
                return self._manage_plugins(**arguments)
            elif function_name == "export_sources":
                return self._export_sources()
            elif function_name == "import_sources":
                return self._import_sources(**arguments)
            elif function_name == "analyze_performance":
                return self._analyze_performance(**arguments)
            else:
                return {"error": f"Unknown function: {function_name}"}
        except Exception as e:
            return {"error": f"Function execution failed: {e!s}"}

    def _scan_for_promotions(self, min_bonus: int = 80) -> dict[str, Any]:
        """Scan for promotions."""
        try:
            seen: set[str] = set()
            alerts = bot.scan_programs(seen)

            # Filter by minimum bonus
            filtered_alerts = [
                (bonus, source, details)
                for bonus, source, details in alerts
                if bonus >= min_bonus
            ]

            return {
                "success": True,
                "promotions_found": len(filtered_alerts),
                "total_scanned": len(alerts),
                "min_bonus": min_bonus,
                "promotions": [
                    {"bonus_percentage": bonus, "source": source, "details": details}
                    for bonus, source, details in filtered_alerts
                ],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _list_sources(self, include_stats: bool = False) -> dict[str, Any]:
        """List all sources."""
        sources = self.store.all()
        result = {"success": True, "total_sources": len(sources), "sources": sources}

        if include_stats:
            # Add basic stats (could be enhanced with actual performance data)
            result["statistics"] = {
                "active_sources": len(sources),
                "monitoring_status": "active" if sources else "no_sources",
            }

        return result

    def _add_source(self, url: str, validate: bool = True) -> dict[str, Any]:
        """Add a new source."""
        if validate:
            # Basic URL validation
            if not url.startswith(("http://", "https://")):
                return {"success": False, "error": "Invalid URL format"}

        success = self.store.add(url)
        return {
            "success": success,
            "message": (
                "Source added successfully"
                if success
                else "Source already exists or is invalid"
            ),
            "url": url,
        }

    def _remove_source(self, identifier: str) -> dict[str, Any]:
        """Remove a source."""
        # Try to remove by URL first, then by index
        sources = self.store.all()

        # Check if it's a URL
        if identifier in sources:
            removed = self.store.remove(identifier)
            return {
                "success": bool(removed),
                "message": f"Removed: {removed}" if removed else "Source not found",
                "removed_url": removed,
            }

        # Check if it's an index
        try:
            idx = int(identifier) - 1  # Convert to 0-based index
            if 0 <= idx < len(sources):
                url_to_remove = sources[idx]
                removed = self.store.remove(url_to_remove)
                return {
                    "success": bool(removed),
                    "message": f"Removed source {idx + 1}: {removed}",
                    "removed_url": removed,
                }
        except ValueError:
            pass

        return {"success": False, "error": "Source not found"}

    def _discover_new_sources(
        self, search_terms: list[str] | None = None
    ) -> dict[str, Any]:
        """Discover new sources using AI."""
        try:
            from miles.ai_source_discovery import ai_update_sources

            added = ai_update_sources()
            return {
                "success": True,
                "new_sources_found": len(added),
                "added_sources": added,
                "search_terms": search_terms
                or ["milhas", "pontos", "transfer", "bonus"],
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _get_schedule(self) -> dict[str, Any]:
        """Get current schedule."""
        from miles.scheduler import get_current_schedule

        config = get_current_schedule()
        return {"success": True, "schedule": config, "timezone": "America/Sao_Paulo"}

    def _set_scan_times(self, hours: list[int]) -> dict[str, Any]:
        """Set scan times."""
        if len(hours) > 6:
            return {"success": False, "error": "Maximum 6 scan times per day"}

        if not all(0 <= h <= 23 for h in hours):
            return {"success": False, "error": "Hours must be between 0 and 23"}

        success = self.schedule_config.set_scan_times(hours)
        return {
            "success": success,
            "scan_times": hours,
            "message": f"Scan times set to: {', '.join(f'{h}:00' for h in sorted(hours))}",
        }

    def _set_update_time(self, hour: int) -> dict[str, Any]:
        """Set update time."""
        success = self.schedule_config.set_update_time(hour)
        return {
            "success": success,
            "update_time": hour,
            "message": f"Source update time set to: {hour}:00",
        }

    def _get_bot_status(self) -> dict[str, Any]:
        """Get comprehensive bot status."""
        import os

        sources_count = len(self.store.all())

        return {
            "success": True,
            "status": {
                "sources_count": sources_count,
                "openai_configured": bool(os.getenv("OPENAI_API_KEY")),
                "redis_configured": bool(os.getenv("REDIS_URL")),
                "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN")),
                "monitoring_active": sources_count > 0,
                "bot_version": "2.0-natural-language",
            },
        }

    def _manage_plugins(
        self, action: str, plugin_name: str | None = None
    ) -> dict[str, Any]:
        """Manage plugins."""
        plugins = discover_plugins()

        if action == "list":
            return {
                "success": True,
                "plugins": {
                    name: {"schedule": plugin.schedule, "categories": plugin.categories}
                    for name, plugin in plugins.items()
                },
            }

        elif action == "test" and plugin_name:
            if plugin_name not in plugins:
                return {"success": False, "error": f"Plugin '{plugin_name}' not found"}

            try:
                plugin = plugins[plugin_name]
                promos = plugin.scrape(datetime.now())
                return {
                    "success": True,
                    "plugin": plugin_name,
                    "test_result": {
                        "promotions_found": len(promos),
                        "schedule": plugin.schedule,
                        "categories": plugin.categories,
                    },
                }
            except Exception as e:
                return {"success": False, "error": f"Plugin test failed: {e!s}"}

        elif action == "info" and plugin_name:
            if plugin_name not in plugins:
                return {"success": False, "error": f"Plugin '{plugin_name}' not found"}

            plugin = plugins[plugin_name]
            return {
                "success": True,
                "plugin_info": {
                    "name": plugin.name,
                    "schedule": plugin.schedule,
                    "categories": plugin.categories,
                    "type": type(plugin).__name__,
                },
            }

        return {"success": False, "error": "Invalid action or missing plugin name"}

    def _export_sources(self) -> dict[str, Any]:
        """Export all sources."""
        sources = self.store.all()
        return {
            "success": True,
            "total_sources": len(sources),
            "sources_text": "\n".join(sources),
            "sources_list": sources,
        }

    def _import_sources(self, urls: list[str]) -> dict[str, Any]:
        """Import multiple sources."""
        added_count = 0
        results = []

        for url in urls:
            if self.store.add(url):
                added_count += 1
                results.append({"url": url, "status": "added"})
            else:
                results.append({"url": url, "status": "already_exists_or_invalid"})

        return {
            "success": True,
            "total_provided": len(urls),
            "successfully_added": added_count,
            "results": results,
        }

    def _analyze_performance(
        self, include_recommendations: bool = True
    ) -> dict[str, Any]:
        """Analyze bot performance."""
        sources = self.store.all()

        analysis = {
            "success": True,
            "performance_metrics": {
                "total_sources": len(sources),
                "monitoring_status": "active" if sources else "inactive",
                "health_score": min(100, len(sources) * 2),  # Simple scoring
            },
        }

        if include_recommendations:
            recommendations = []
            if len(sources) < 10:
                recommendations.append(
                    "Consider adding more sources for better coverage"
                )
            if len(sources) > 100:
                recommendations.append(
                    "Consider removing low-quality sources to improve performance"
                )

            analysis["recommendations"] = recommendations

        return analysis


# Global instance
function_registry = FunctionRegistry()
