import httpx
from typing import Iterable

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

async def get_simple_price(ids: Iterable[str], vs_currency: str = "usd") -> dict[str, float]:
    ids_csv = ",".join(ids)
    params = {"ids": ids_csv, "vs_currencies": vs_currency}
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{COINGECKO_BASE}/simple/price", params=params)
        r.raise_for_status()
        data = r.json()
        return {k: float(v.get(vs_currency, 0.0)) for k, v in data.items()}
