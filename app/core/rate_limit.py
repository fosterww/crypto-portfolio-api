import time
from fastapi import HTTPException
from app.core.cache import get_redis

async def rate_limit_sliding(key: str, limit: int, window_sec: int):
    """
    Redis ZSET: ключ — timestamps (score=ts, member=ts).
    Очищаем старые, считаем оставшиеся.
    """
    now = time.time()
    r = await get_redis()
    k = f"rlz:{key}"
    pipe = r.pipeline()
    pipe.zremrangebyscore(k, 0, now - window_sec)
    pipe.zadd(k, {str(now): now})
    pipe.zcard(k)
    pipe.expire(k, window_sec)
    _, _, count, _ = await pipe.execute()
    if count > limit:
        raise HTTPException(429, detail="Too many requests")
