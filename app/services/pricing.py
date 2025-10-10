import json
from typing import Sequence, Iterable
from sqlalchemy.orm import Session
from app.core.cache import get_redis
from app.services import coingecko
from app.db.models import Asset


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
    symbols = [s.upper() for s in _ensure_iterable_ids(symbols)]
    vs = (vs or "usd").lower()

    assets: list[Asset] = list(db.query(Asset).filter(Asset.symbol.in_(symbols)).all())
    sym_to_id = {a.symbol.upper(): a.coingecko_id for a in assets}
    ids_list = [sym_to_id[s] for s in symbols if s in sym_to_id]

    if not ids_list:
        return {}

    key = _cache_key(vs, ids_list)
    r = await get_redis()

    cached = await r.get(key)
    if cached:
        try:
            data = json.loads(cached)
            return {k.upper(): float(v) for k, v in data.items()}
        except Exception:
            pass

    cg = await coingecko.get_simple_price(ids_list, vs_currency=vs)

    id_to_sym = {v: k for k, v in sym_to_id.items()}
    data_by_symbol: dict[str, float] = {}
    for coin_id, price_map in cg.items():
        sym = id_to_sym.get(coin_id)
        if not sym:
            continue
        data_by_symbol[sym.upper()] = _extract_price(price_map, vs)

    await r.setex(key, ttl, json.dumps(data_by_symbol))
    return data_by_symbol
