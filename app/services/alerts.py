from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.models import Alert, Asset, AlertDirection, AlertChannel
from app.services.pricing import get_prices_cached
from app.core.cache import get_redis
from app.core.config import settings
from app.services.notifier import send_telegram, send_email

def _cooldown_key(user_id: int, alert_id: int) -> str:
    return f"alert:{user_id}:{alert_id}:cooldown"

async def process_alerts(db: Session):
    rows = (
        db.query(Alert, Asset)
        .join(Asset, Asset.id == Alert.asset_id)
        .filter(Alert.is_active == True)
        .all()
    )
    if not rows:
        return

    symbols = {asset.symbol.upper() for _, asset in rows}
    prices = await get_prices_cached(db, list(symbols), vs=settings.DEFAULT_VS.lower(), ttl=60)

    r = await get_redis()
    cooldown = int(settings.ALERT_COOLDAWN_SEC)
    now = datetime.utcnow()

    for a, asset in rows:
        sym = asset.symbol.upper()
        price = prices.get(sym)
        if price is None:
            continue

        threshold = float(a.threshold_price) if isinstance(a.threshold_price, Decimal) else float(a.threshold_price)

        triggered = (
            (a.direction == AlertDirection.above and price >= threshold) or
            (a.direction == AlertDirection.below and price <= threshold)
        )
        if not triggered:
            continue

        key = _cooldown_key(a.user_id, a.id)
        if await r.get(key):
            continue

        text = f"⚠️ {sym}: price={price} crossed {a.direction} {threshold}"
        ok = False
        if a.channel == AlertChannel.telegram:
            ok = await send_telegram(text)
        elif a.channel == AlertChannel.email:
            ok = send_email("user@example.com", f"Alert {sym}", text)

        if ok:
            a.last_triggered_at = now
            db.add(a); db.commit()
            await r.setex(key, cooldown, "1")
