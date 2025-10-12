from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.pricing import get_prices_cached
from app.core.config import settings
from app.schemas.assets import PricesOut
from app.core.rate_limit import rate_limit_sliding

router = APIRouter()

@router.get("", response_model=PricesOut)
async def get_prices(symbols: str = Query(..., description="Comma-seperated symbols: BTC,ETH"),
                     vs: str = Query(None, description="Fiat crypto denom, e.g. usd, eur"),
                     db: Session = Depends(get_db)):
    await rate_limit_sliding(key="prices", limit=60, window_sec=60)
    vs = (vs or settings.DEFAULT_VS).lower()
    symbol_list = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    if not symbol_list:
        raise HTTPException(status_code=400, detail="No symbols provided")
    prices = await get_prices_cached(db, symbol_list, vs=vs, ttl=60)
    return PricesOut(vs=vs, prices=prices)