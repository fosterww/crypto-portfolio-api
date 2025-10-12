import asyncio, httpx
from typing import Callable, Awaitable

async def with_retries(task: Callable[[], Awaitable[httpx.Response]],
                       attempts: int = 3, base_delay: float = 0.5):
    last_exc = None
    for i in range(attempts):
        try:
            resp = await task()
            resp.raise_for_status()
            return resp
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            last_exc = e
            if i == attempts - 1:
                raise
            await asyncio.sleep(base_delay * (2 ** i))
    raise last_exc
