from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Portfolio, User, Position, Asset
from app.schemas.portfolio import (
    PortfolioCreateIn, PortfolioUpdate, PortfolioOut,
    PortfolioSummaryOut, PositionSummaryOut
)
from app.schemas.common import PaginationParams
from app.core.security import get_current_user
from decimal import Decimal
from app.core.config import settings
from app.services import coingecko
import inspect
import re
from typing import Iterable, Dict, Any

router = APIRouter()


def _norm_symbol(s: str) -> str:
    s = (s or "").strip().upper()
    m = re.match(r"[A-Z]{2,6}", s)
    return m.group(0) if m else s


async def _call_prices(ids: Iterable[str], vs: str) -> Dict[str, Any]:
    ids_list = [i for i in map(lambda x: (x or "").strip(), ids) if i]
    candidates = [ids_list, ",".join(ids_list)]

    last_res: Any = {}
    for candidate in candidates:
        res = coingecko.get_simple_price(candidate, vs_currency=vs)
        if inspect.isawaitable(res):
            res = await res
        last_res = res
        if isinstance(res, dict) and res:
            return res
    return last_res if isinstance(last_res, dict) else {}

@router.post("", response_model=PortfolioOut, status_code=201)
def create_portfolio(payload: PortfolioCreateIn,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = Portfolio(user_id=user.id, name=payload.name)
    db.add(p); db.commit(); db.refresh(p)
    return p

@router.patch("/{pid}", response_model=PortfolioOut)
def patch_portfolio(pid: int, payload: PortfolioUpdate,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    p.name = payload.name
    db.commit(); db.refresh(p)
    return p

@router.get("", response_model=list[PortfolioOut])
def list_portfolios(p: PaginationParams = Depends(),
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    q = (db.query(Portfolio)
           .filter(Portfolio.user_id == user.id)
           .order_by(Portfolio.id.desc())
           .limit(p.limit).offset(p.offset))
    return q.all()

@router.get("/", response_model=list[PortfolioOut])
def list_portfolios_alias(p: PaginationParams = Depends(),
                          db: Session = Depends(get_db),
                          user: User = Depends(get_current_user)):
    return list_portfolios(p=p, db=db, user=user)

@router.get("/{pid}", response_model=PortfolioOut)
def get_portfolio(pid: int,
                  db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    return p


@router.delete("/{pid}", status_code=204)
def delete_portfolio(pid: int,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    p = db.query(Portfolio).filter(Portfolio.id == pid, Portfolio.user_id == user.id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Portfolio not found")
    db.delete(p); db.commit()
    return


@router.get("/{pid}/summary", response_model=PortfolioSummaryOut)
async def portfolio_summary(pid: int,
                            vs: str | None = None,
                            db: Session = Depends(get_db),
                            user: User = Depends(get_current_user)):
    vs = (vs or settings.DEFAULT_VS).lower()

    positions = db.query(Position).filter(Position.portfolio_id == pid).all()
    if not positions:
        return PortfolioSummaryOut(
            portfolio_id=pid, vs=vs,
            total_value=0.0, total_cost=0.0, total_pnl=0.0, pnl_pct=0.0, positions=[]
        )

    asset_ids = {p.asset_id for p in positions if p.asset_id is not None}
    assets = db.query(Asset).filter(Asset.id.in_(asset_ids)).all() if asset_ids else []
    assets_by_id = {a.id: a for a in assets}

    rows = [(p, assets_by_id.get(p.asset_id)) for p in positions if assets_by_id.get(p.asset_id)]
    if not rows:
        return PortfolioSummaryOut(
            portfolio_id=pid, vs=vs,
            total_value=0.0, total_cost=0.0, total_pnl=0.0, pnl_pct=0.0, positions=[]
        )

    if not rows:
        return PortfolioSummaryOut(
            portfolio_id=pid, vs=vs,
            total_value=0.0, total_cost=0.0, total_pnl=0.0, pnl_pct=0.0, positions=[]
        )

    symbols = sorted({
        _norm_symbol(a.symbol)
        for (_p, a) in rows
        if a and a.symbol
    })

    symbol_to_id_fallback: dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
    }
    for _p, a in rows:
        if a and a.symbol and a.coingecko_id:
            symbol_to_id_fallback[_norm_symbol(a.symbol)] = (a.coingecko_id or "").strip().lower()

    coin_ids = [symbol_to_id_fallback[s] for s in symbols if s in symbol_to_id_fallback]
    seen = set()
    coin_ids = [cid for cid in coin_ids if not (cid in seen or seen.add(cid))]
    if not coin_ids:
        coin_ids = ["bitcoin", "ethereum"]

    res = coingecko.get_simple_price(coin_ids, vs_currency=vs)
    if inspect.isawaitable(res):
        res = await res

    if not isinstance(res, dict) or not res:
        res = await _call_prices(coin_ids, vs)
    if (not isinstance(res, dict) or not res) and symbols:
        res = await _call_prices(symbols, vs)

    def _extract(v: dict | float | int) -> float:
        return float(v.get(vs, 0.0)) if isinstance(v, dict) else float(v)

    id_to_symbol = {v: k for k, v in symbol_to_id_fallback.items()}
    prices_by_symbol: dict[str, float] = {}
    symbols_set = set(symbols)

    if isinstance(res, dict):
        for k, v in res.items():
            price = _extract(v)
            sym_from_id = id_to_symbol.get((k or "").strip().lower())
            if sym_from_id:
                prices_by_symbol[sym_from_id.upper()] = price
            k_up = (k or "").strip().upper()
            if k_up in symbols_set:
                prices_by_symbol[k_up] = price

    total_value = Decimal("0")
    total_cost = Decimal("0")
    items: list[PositionSummaryOut] = []

    for pos, asset in rows:
        sym = _norm_symbol(asset.symbol) if asset else ""
        qty = Decimal(pos.qty)
        avg = Decimal(pos.avg_buy_price)

        price_f = prices_by_symbol.get(sym)

        if price_f is None and asset and getattr(asset, "coingecko_id", None) and isinstance(res, dict):
            cid = (asset.coingecko_id or "").strip().lower()
            if cid in res:
                vv = res[cid]
                price_f = _extract(vv)

        price = Decimal(str(price_f or 0.0))

        value = qty * price
        cost = qty * avg
        pnl = value - cost

        total_value += value
        total_cost += cost

        items.append(PositionSummaryOut(
            asset_symbol=asset.symbol if asset else None,
            qty=str(qty),
            avg_buy_price=str(avg),
            price=price,
            value=value,
            pnl=pnl,
        ))

    total_pnl = total_value - total_cost
    pnl_pct = float((total_pnl / total_cost * Decimal("100")) if total_cost > 0 else Decimal("0"))

    return PortfolioSummaryOut(
        portfolio_id=pid,
        vs=vs,
        total_value=float(total_value),
        total_cost=float(total_cost),
        total_pnl=float(total_pnl),
        pnl_pct=pnl_pct,
        positions=items,
    )
