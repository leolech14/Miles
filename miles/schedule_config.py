from __future__ import annotations

import json
import os
from typing import Optional, Any, Dict
import redis


class ScheduleConfig:
    """Manages schedule configuration with Redis persistence"""
    
    def __init__(self) -> None:
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        self.r: Optional[redis.Redis] = None
        if url != "not_set":
            try:
                redis_client = redis.Redis.from_url(url, decode_responses=True)
                redis_client.ping()
                self.r = redis_client
            except Exception:
                pass
    
    def _key(self) -> str:
        return "schedule:config"
    
    def get_config(self) -> Dict[str, Any]:
        """Get current schedule configuration"""
        default_config = {
            "update_hour": 6,
            "scan_hours": [9, 18],
            "timezone": "America/Sao_Paulo"
        }
        
        if not self.r:
            return default_config
            
        raw = self.r.get(self._key())
        if raw:
            try:
                return {**default_config, **json.loads(str(raw))}
            except json.JSONDecodeError:
                return default_config
        return default_config
    
    def set_update_time(self, hour: int) -> bool:
        """Set the hour for source updates"""
        if not 0 <= hour <= 23:
            return False
            
        config = self.get_config()
        config["update_hour"] = hour
        return self._save_config(config)
    
    def set_scan_times(self, hours: list[int]) -> bool:
        """Set the hours for promotion scans"""
        if not hours or not all(0 <= h <= 23 for h in hours):
            return False
            
        config = self.get_config()
        config["scan_hours"] = sorted(list(set(hours)))  # Remove duplicates and sort
        return self._save_config(config)
    
    def _save_config(self, config: Dict[str, Any]) -> bool:
        """Save configuration to Redis"""
        if not self.r:
            return False
            
        try:
            self.r.set(self._key(), json.dumps(config))
            return True
        except Exception:
            return False
