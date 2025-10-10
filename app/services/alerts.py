from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.models import Alert, Asset, User, AlertDirection, AlertChannel
from app.services.pricing import get_prices_cached
from app.core.cache import get_redis
from app.core.config import settings
from app.services.notifier import send_telegram, send_email

def _cooldown_key(user_id: int, alert_id: int) -> str:
    return f"alert:{user_id}:{alert_id}:cooldown"

async def process_alerts(db: Session):
    alerts = db.query(Alert, Asset).join(Asset, Asset.id == Alert.asset_id).filter(Alert.is_active == True).all()
    if not alerts:
        return
    
    symbols = sorted({asset.symbol for (_a, asset) in alerts})
    prices = await get_prices_cached(db, symbols, vs=settings.DEFAULT_VS, ttl=60)

    r = await get_redis()
    now = datetime.utcnow()
    cooldown = settings.ALERT_COOLDOWN_SEC

    for a, asset in alerts:
        price = Decimal(str(prices.get(asset.symbol, 0.0)))
        threshold = Decimal(a.threshold_price)

        should_trigger = False
        if a.direction == AlertDirection.above and price >= threshold:
            should_trigger = True
        elif a.direction == AlertDirection.below and price <= threshold:
            should_trigger = True

        if not should_trigger:
            continue

        key = _cooldown_key(a.user_id, a.id)
        if await r.get(key):
            continue

        text = f"⚠️ {asset.symbol} price={price} crossed {a.direction} {threshold}"
        ok = False
        if a.channel == AlertChannel.telegram:
            ok = await send_telegram(text)
        elif a.channel == AlertChannel.email:
            ok = send_email("user@example.com", f"Alert {asset.symbol}", text)
        
        if ok:
            a.last_triggered_at = now
            db.add(a); db.commit()
            await r.setex(key, cooldown, b"1")