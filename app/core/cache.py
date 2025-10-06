import redis.asyncio as redis
from functools import lru_cache
from app.core.config import settings

@lru_cache(size=1)
def _redis():
    return redis.from_url(settings.REDIS_URL, decode_responses=True)

async def close_redis():
    r = _redis()
    await r.Close()

async def get_redis():
    return _redis()