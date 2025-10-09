import json
from typing import Sequence, Iterable
from app.core.cache import get_redis
from app.services import coingecko
from app.db.models import Asset
from sqlalchemy.orm import Session
import inspect

def _cache_key(vs: str, ids: Sequence[str]) -> str:
    return f"prices:v3:{vs}:{','.join(sorted(ids))}"

def _ensure_iterable_ids(ids_param) -> list[str]:
    if isinstance(ids_param, str):
        return [x.strip() for x in ids_param.split(",") if x.strip()]
    if isinstance(ids_param, Iterable):
        return list(ids_param)
    return [str(ids_param)]

def _extract_price(v, vs: str) -> float:
    if isinstance(v, dict):
        return float(v.get(vs, 0.0))
    try:
        return float(v)
    except Exception:
        return 0.0

async def get_prices_cached(db: Session, symbols: Sequence[str], vs: str = "usd", ttl: int = 60) -> dict[str, float]:
    symbols = [s.upper() for s in symbols if s]
    if not symbols:
        return {}

    rows = db.query(Asset).filter(Asset.symbol.in_(symbols)).all()
    sym_to_id: dict[str, str] = {a.symbol.upper(): a.coingecko_id for a in rows if a.coingecko_id}

    fallback_map = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
    }
    for s in symbols:
        if s not in sym_to_id and s in fallback_map:
            sym_to_id[s] = fallback_map[s]

    ids = [sym_to_id[s] for s in symbols if s in sym_to_id]
    if not ids:
        return {}

    r = await get_redis()
    key = _cache_key(vs, ids)

    raw = await r.get(key)
    if raw:
        data = json.loads(raw)
        inv = {v: k for k, v in sym_to_id.items()}
        if any(k in inv for k in data.keys()):
            data = {inv.get(k, k): float(v) for k, v in data.items()}
        else:
            data = {str(k).upper(): float(v) for k, v in data.items()}
        await r.setex(key, ttl, json.dumps(data))
        if all(s in data for s in symbols):
            return data

    res = coingecko.get_simple_price(ids, vs_currency=vs)
    if inspect.isawaitable(res):
        res = await res

    cg = res 
    ids_list = _ensure_iterable_ids(ids)

    prices_by_id: dict[str, float] = {}
    if isinstance(cg, dict):
        for coin_id in ids_list:
            if coin_id in cg:
                prices_by_id[coin_id] = _extract_price(cg[coin_id], vs)

    inv = {v: k for k, v in sym_to_id.items()}
    data_by_symbol: dict[str, float] = {}
    for cid, price in prices_by_id.items():
        sym = inv.get(cid)
        if sym:
            data_by_symbol[sym.upper()] = float(price)

    data_by_symbol = {k.upper(): float(v) for k, v in data_by_symbol.items()}
    await r.setex(key, ttl, json.dumps(data_by_symbol))
    return data_by_symbol
