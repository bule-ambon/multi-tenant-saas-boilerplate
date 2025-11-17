"""
Rate Limiting Middleware
Implements per-tenant and per-user rate limiting
"""
import logging
import time
from typing import Callable, Dict, Optional

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import redis.asyncio as redis

from app.core.config import settings

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Advanced rate limiting middleware with Redis backend
    Supports tenant-level and user-level rate limits
    """

    def __init__(self, app):
        super().__init__(app)
        self.enabled = settings.RATE_LIMIT_ENABLED
        self.redis_client: Optional[redis.Redis] = None

        # Rate limit configuration
        self.limits = {
            "per_minute": settings.RATE_LIMIT_PER_MINUTE,
            "per_hour": settings.RATE_LIMIT_PER_HOUR,
        }

    async def init_redis(self):
        """Initialize Redis connection"""
        if not self.redis_client:
            try:
                self.redis_client = redis.from_url(
                    str(settings.REDIS_URL),
                    encoding="utf-8",
                    decode_responses=True,
                )
                await self.redis_client.ping()
                logger.info("Rate limiter Redis connection established")
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.enabled = False

    async def check_rate_limit(
        self, key: str, limit: int, window: int
    ) -> tuple[bool, Dict[str, int]]:
        """
        Check if rate limit is exceeded using sliding window
        Returns: (is_allowed, rate_limit_info)
        """
        if not self.redis_client:
            await self.init_redis()

        if not self.redis_client:
            # If Redis is not available, allow the request
            return True, {}

        current_time = int(time.time())
        window_start = current_time - window

        try:
            # Use Redis sorted set for sliding window
            pipe = self.redis_client.pipeline()

            # Remove old entries outside the window
            pipe.zremrangebyscore(key, 0, window_start)

            # Count requests in current window
            pipe.zcard(key)

            # Add current request
            pipe.zadd(key, {str(current_time): current_time})

            # Set expiration
            pipe.expire(key, window)

            # Execute pipeline
            results = await pipe.execute()

            current_count = results[1]
            remaining = max(0, limit - current_count - 1)

            rate_limit_info = {
                "limit": limit,
                "remaining": remaining,
                "reset": current_time + window,
            }

            # Check if limit exceeded
            if current_count >= limit:
                return False, rate_limit_info

            return True, rate_limit_info

        except Exception as e:
            logger.error(f"Rate limit check error: {e}")
            # On error, allow the request
            return True, {}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and apply rate limiting"""

        if not self.enabled:
            return await call_next(request)

        # Skip rate limiting for health checks and docs
        excluded_paths = ["/health", "/metrics", "/docs", "/redoc"]
        if any(request.url.path.startswith(path) for path in excluded_paths):
            return await call_next(request)

        # Build rate limit key
        tenant_id = getattr(request.state, "tenant_id", None)
        user_id = getattr(request.state, "user_id", None)
        ip_address = request.client.host if request.client else "unknown"

        # Priority: user > tenant > ip
        if user_id:
            key_prefix = f"rate_limit:user:{user_id}"
        elif tenant_id:
            key_prefix = f"rate_limit:tenant:{tenant_id}"
        else:
            key_prefix = f"rate_limit:ip:{ip_address}"

        # Check per-minute limit
        minute_key = f"{key_prefix}:minute"
        minute_allowed, minute_info = await self.check_rate_limit(
            minute_key, self.limits["per_minute"], 60
        )

        if not minute_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": 60,
                },
                headers={
                    "X-RateLimit-Limit": str(minute_info["limit"]),
                    "X-RateLimit-Remaining": str(minute_info["remaining"]),
                    "X-RateLimit-Reset": str(minute_info["reset"]),
                    "Retry-After": "60",
                },
            )

        # Check per-hour limit
        hour_key = f"{key_prefix}:hour"
        hour_allowed, hour_info = await self.check_rate_limit(
            hour_key, self.limits["per_hour"], 3600
        )

        if not hour_allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "rate_limit_exceeded",
                    "detail": "Hourly rate limit exceeded. Please try again later.",
                    "retry_after": 3600,
                },
                headers={
                    "X-RateLimit-Limit": str(hour_info["limit"]),
                    "X-RateLimit-Remaining": str(hour_info["remaining"]),
                    "X-RateLimit-Reset": str(hour_info["reset"]),
                    "Retry-After": "3600",
                },
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if minute_info:
            response.headers["X-RateLimit-Limit"] = str(minute_info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(minute_info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(minute_info["reset"])

        return response
