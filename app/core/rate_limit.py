import time
from fastapi import HTTPException
from app.core.cache import get_redis

async def rate_limit(key: str, limit: int, window_sec: int):
    now = int(time.time())
    r = await get_redis()
    rk = f"rl:{key}"
    count = await r.incr(rk)
    if count == 1:
        await r.expire(rk, window_sec)
    if count > limit:
        ttl = await r.ttl(rk)
        raise HTTPException(429, detail=f"Too many requests. Retry in {ttl}s" if ttl > 0 else "Too many requests")