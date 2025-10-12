from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models import Alert, Asset, Portfolio, User
from app.schemas.alerts import AlertCreateIn, AlertUpdate, AlertOut
from app.schemas.common import PaginationParams
from app.core.security import get_current_user
from app.core.cache import get_redis
from app.services.pricing import get_prices_cached
from app.core.rate_limit import rate_limit

router = APIRouter()

def _side(price: float, threshold: float) -> str:
    return "above" if price >= threshold else "below"

@router.post("", status_code=201, response_model=AlertOut)
async def create_alert(payload: AlertCreateIn,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    await rate_limit(key=f"user:{user.id}:alerts:list", limit=120, window_sec=60)
    asset = db.query(Asset).filter(Asset.id == payload.asset_id).first()
    if not asset:
        raise HTTPException(status_code=400, detail="Asset not found")
    
    a = Alert(
        user_id=user.id,
        asset_id=payload.asset_id,
        direction=payload.direction,
        threshold_price=payload.threshold_price,
        channel=payload.channel,
        is_active=True,
    )
    db.add(a); db.flush(); db.commit(); db.refresh(a)

    r = await get_redis()
    sym = asset.symbol.upper()
    prices = await get_prices_cached(db, [sym], vs="usd", ttl=60)
    price = float(prices.get(sym, 0.0))
    if price:
        await r.set(f"alert:{a.id}:state", _side(price, float(a.threshold_price)))
    return a

@router.get("", response_model=list[AlertOut])
def list_alerts(p: PaginationParams = Depends(),
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    q = (db.query(Alert)
         .filter(Alert.user_id == user.id)
         .order_by(Alert.id.desc())
         .limit(p.limit).offset(p.offset))
    return q.all()

@router.patch("/{alert_id}", response_model=AlertOut)
async def update_alert(alert_id: int,
                       payload: AlertUpdate,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    a = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(a, field, value)
    db.commit(); db.refresh(a)

    r = await get_redis()
    await r.delete(
        f"alert:{a.id}:state",
        f"alert:{a.user_id}:{a.id}:cooldown"
    )
    return a

@router.delete("/{alert_id}", status_code=204)
async def delete_alert(alert_id: int,
                       db: Session = Depends(get_db),
                       user: User = Depends(get_current_user)):
    a = db.query(Alert).filter(Alert.id == alert_id, Alert.user_id == user.id).first()
    if not a:
        raise HTTPException(status_code=404, detail="Alert not found")

    r = await get_redis()
    await r.delete(
        f"alert:{a.id}:state",
        f"alert:{a.user_id}:{a.id}:cooldown"
    )

    db.delete(a); db.commit()
    return
