"""Advanced rate limiting system for Miles bot."""

from __future__ import annotations

import logging
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import dataclass
from enum import Enum
from typing import Any, AsyncIterator, Callable, Dict, Optional

import redis

logger = logging.getLogger("miles.rate_limiter")


class RateLimitType(Enum):
    """Types of rate limits."""

    TELEGRAM_COMMAND = "telegram_command"
    OPENAI_REQUEST = "openai_request"
    SOURCE_SCAN = "source_scan"
    PLUGIN_EXECUTION = "plugin_execution"
    REDIS_OPERATION = "redis_operation"
    USER_OPERATION = "user_operation"


@dataclass
class RateLimit:
    """Rate limit configuration."""

    requests: int  # Number of requests allowed
    window: int  # Time window in seconds
    burst: int  # Burst capacity (requests allowed instantly)


# Default rate limits
DEFAULT_LIMITS = {
    RateLimitType.TELEGRAM_COMMAND: RateLimit(
        requests=10, window=60, burst=5
    ),  # 10/min, burst 5
    RateLimitType.OPENAI_REQUEST: RateLimit(
        requests=20, window=60, burst=3
    ),  # 20/min, burst 3
    RateLimitType.SOURCE_SCAN: RateLimit(
        requests=5, window=300, burst=2
    ),  # 5/5min, burst 2
    RateLimitType.PLUGIN_EXECUTION: RateLimit(
        requests=30, window=60, burst=10
    ),  # 30/min, burst 10
    RateLimitType.REDIS_OPERATION: RateLimit(
        requests=1000, window=60, burst=100
    ),  # 1000/min, burst 100
    RateLimitType.USER_OPERATION: RateLimit(
        requests=30, window=60, burst=10
    ),  # 30/min per user, burst 10
}


class RateLimiter:
    """Advanced rate limiter with Redis backend and fallback to in-memory."""

    def __init__(self, redis_client: Optional[redis.Redis[str]] = None):
        self.redis = redis_client
        self.local_buckets: Dict[str, deque[float]] = defaultdict(lambda: deque())
        self.local_burst_tokens: Dict[str, int] = defaultdict(int)
        self.limits = DEFAULT_LIMITS.copy()

    def set_limit(self, limit_type: RateLimitType, limit: RateLimit) -> None:
        """Update rate limit for a specific type."""
        self.limits[limit_type] = limit
        logger.info(f"Updated rate limit for {limit_type.value}: {limit}")

    async def is_allowed(
        self, limit_type: RateLimitType, identifier: str = "global", cost: int = 1
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Check if request is allowed under rate limit.

        Args:
            limit_type: Type of rate limit to check
            identifier: Unique identifier (user_id, ip, etc.)
            cost: Cost of this request (default 1)

        Returns:
            Tuple of (allowed, metadata) where metadata contains:
            - remaining: requests remaining in window
            - reset_time: when window resets
            - retry_after: seconds to wait if limited
        """
        limit = self.limits.get(limit_type)
        if not limit:
            # No limit configured, allow all
            return True, {"remaining": 999, "reset_time": time.time() + 60}

        key = f"rate_limit:{limit_type.value}:{identifier}"

        if self.redis is not None:
            return await self._check_redis_limit(key, limit, cost)
        else:
            return await self._check_local_limit(key, limit, cost)

    async def _check_redis_limit(
        self, key: str, limit: RateLimit, cost: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using Redis sliding window."""
        try:
            current_time = time.time()
            window_start = current_time - limit.window

            # Use Redis pipeline for atomic operations
            pipe = self.redis.pipeline()

            # Clean old entries
            pipe.zremrangebyscore(key, 0, window_start)

            # Count current requests
            pipe.zcard(key)

            # Execute pipeline
            results = pipe.execute()
            current_count = results[1]

            # Check burst capacity first
            burst_key = f"{key}:burst"
            burst_tokens = int(self.redis.get(burst_key) or limit.burst)

            if burst_tokens > 0 and cost <= burst_tokens:
                # Use burst capacity
                pipe = self.redis.pipeline()
                pipe.decrby(burst_key, cost)
                pipe.expire(burst_key, limit.window)
                pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, limit.window)
                pipe.execute()

                return True, {
                    "remaining": limit.requests - current_count,
                    "reset_time": current_time + limit.window,
                    "burst_used": True,
                }

            # Check regular rate limit
            if current_count + cost <= limit.requests:
                # Add request timestamps
                pipe = self.redis.pipeline()
                for _ in range(cost):
                    pipe.zadd(key, {str(current_time): current_time})
                pipe.expire(key, limit.window)
                pipe.execute()

                # Refill burst tokens if time has passed
                if burst_tokens < limit.burst:
                    self.redis.setex(burst_key, limit.window, limit.burst)

                return True, {
                    "remaining": limit.requests - current_count - cost,
                    "reset_time": current_time + limit.window,
                }
            else:
                # Rate limited
                oldest_request = self.redis.zrange(key, 0, 0, withscores=True)
                retry_after = limit.window
                if oldest_request:
                    retry_after = min(
                        retry_after,
                        int(limit.window - (current_time - oldest_request[0][1])),
                    )

                return False, {
                    "remaining": 0,
                    "reset_time": current_time + limit.window,
                    "retry_after": max(1, int(retry_after)),
                }

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Fall back to local checking
            return await self._check_local_limit(key, limit, cost)

    async def _check_local_limit(
        self, key: str, limit: RateLimit, cost: int
    ) -> tuple[bool, Dict[str, Any]]:
        """Check rate limit using local in-memory storage."""
        current_time = time.time()
        window_start = current_time - limit.window

        # Clean old entries
        bucket = self.local_buckets[key]
        while bucket and bucket[0] < window_start:
            bucket.popleft()

        # Check burst capacity
        burst_tokens = self.local_burst_tokens.get(key, limit.burst)
        if burst_tokens >= cost:
            self.local_burst_tokens[key] = burst_tokens - cost
            bucket.append(current_time)
            return True, {
                "remaining": limit.requests - len(bucket),
                "reset_time": current_time + limit.window,
                "burst_used": True,
            }

        # Check regular limit
        if len(bucket) + cost <= limit.requests:
            for _ in range(cost):
                bucket.append(current_time)

            # Refill burst tokens
            self.local_burst_tokens[key] = limit.burst

            return True, {
                "remaining": limit.requests - len(bucket),
                "reset_time": current_time + limit.window,
            }
        else:
            # Rate limited
            retry_after = limit.window
            if bucket:
                retry_after = min(
                    retry_after, int(limit.window - (current_time - bucket[0]))
                )

            return False, {
                "remaining": 0,
                "reset_time": current_time + limit.window,
                "retry_after": max(1, int(retry_after)),
            }

    @asynccontextmanager
    async def limit(
        self, limit_type: RateLimitType, identifier: str = "global", cost: int = 1
    ) -> AsyncIterator[Dict[str, Any]]:
        """Context manager for rate limiting."""
        allowed, metadata = await self.is_allowed(limit_type, identifier, cost)

        if not allowed:
            from miles.metrics import telegram_commands_total

            telegram_commands_total.labels("rate_limited", "error").inc()

            raise RateLimitExceeded(
                f"Rate limit exceeded for {limit_type.value}",
                retry_after=metadata.get("retry_after", 60),
                metadata=metadata,
            )

        yield metadata

    async def get_stats(
        self, limit_type: RateLimitType, identifier: str = "global"
    ) -> Dict[str, Any]:
        """Get current rate limit statistics."""
        limit = self.limits.get(limit_type)
        if not limit:
            return {"error": "No limit configured"}

        allowed, metadata = await self.is_allowed(
            limit_type, identifier, cost=0
        )  # Cost 0 = just check

        return {
            "limit_type": limit_type.value,
            "identifier": identifier,
            "requests_per_window": limit.requests,
            "window_seconds": limit.window,
            "burst_capacity": limit.burst,
            "currently_allowed": allowed,
            **metadata,
        }


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int, metadata: Dict[str, Any]):
        super().__init__(message)
        self.retry_after = retry_after
        self.metadata = metadata


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        try:
            import os
            import redis

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            if redis_url != "not_set":
                redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
                redis_client.ping()  # Test connection
                _rate_limiter = RateLimiter(redis_client)
            else:
                _rate_limiter = RateLimiter()
        except Exception as e:
            logger.warning(f"Failed to connect to Redis for rate limiting: {e}")
            _rate_limiter = RateLimiter()

    return _rate_limiter


# Convenience decorators
def rate_limit(limit_type: RateLimitType, identifier_func: Optional[Callable] = None):
    """Decorator for rate limiting functions."""

    def decorator(func: Callable) -> Callable:
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            identifier = "global"
            if identifier_func:
                identifier = identifier_func(*args, **kwargs)

            limiter = get_rate_limiter()
            async with limiter.limit(limit_type, identifier):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def get_user_id_from_update(update: Any, *args: Any, **kwargs: Any) -> str:
    """Helper to extract user ID from Telegram update."""
    if hasattr(update, "effective_user") and update.effective_user:
        return str(update.effective_user.id)
    return "anonymous"
