"""Redis-backed rate limits for hot paths (auth, upload). Fail-open if Redis is down."""
from fastapi import HTTPException, Request

from service.redis_service import get_redis_service


async def enforce_rate_limit(request: Request, bucket: str, limit: int, window_sec: int = 60) -> None:
    ip = (request.client.host if request.client else None) or "unknown"
    redis = await get_redis_service()
    ok, _ = await redis.check_rate_limit(f"rl:{bucket}:{ip}", limit, window_sec)
    if not ok:
        raise HTTPException(status_code=429, detail="Too many requests. Try again later.")
