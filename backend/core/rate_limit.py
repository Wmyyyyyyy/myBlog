from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from redis.asyncio import Redis
import time

# Redis key format: rate_limit:{user_id}:{endpoint}:{minute}
# Use fixed window (minute timestamp // 60)

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis: Redis):
        super().__init__(app)
        self.redis = redis
        self.limits = {
            "/api/dynamics/feed": 30,  # per minute
            "/api/interactions/favorites": 20,
            "/api/interactions/likes": 20,
            "/api/interactions/follows": 20,
            "default": 60
        }

    async def dispatch(self, request: Request, call_next):
        # Skip if no auth user
        user_id = getattr(request.state, 'user_id', None)
        if not user_id:
            return await call_next(request)

        # Determine limit
        path = request.url.path
        limit = self.limits.get(path, self.limits["default"])

        # Check rate limit
        minute = int(time.time()) // 60
        key = f"rate_limit:{user_id}:{path}:{minute}"

        count = await self.redis.incr(key)
        if count == 1:
            await self.redis.expire(key, 60)

        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests",
                headers={"Retry-After": "60", "X-RateLimit-Limit": str(limit)}
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(max(0, limit - count))
        return response
