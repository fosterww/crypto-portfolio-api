import httpx
from app.utils.http import with_retries

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

async def get_simple_price(ids, vs_currency="usd") -> dict[str, float]:
    ids_csv = ",".join(ids)
    params = {"ids": ids_csv, "vs_currencies": vs_currency}
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await with_retries(lambda: client.get(f"{COINGECKO_BASE}/simple/price", params=params))
        data = resp.json()
        return {k: float(v.get(vs_currency, 0.0)) for k, v in data.items()}
