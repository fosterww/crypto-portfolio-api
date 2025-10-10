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
    rows: list[tuple[Alert, Asset]] = (
        db.query(Alert, Asset)
        .join(Asset, Asset.id == Alert.asset_id)
        .filter(Alert.is_active == True)
        .all()
    )
    if not rows:
        return

    symbols = sorted({asset.symbol.upper() for _, asset in rows})
    prices_by_symbol = await get_prices_cached(db, symbols, vs=settings.DEFAULT_VS.lower(), ttl=60)

    r = await get_redis()
    cooldown_sec = int(settings.ALERT_COOLDOWN_SEC)
    now = datetime.utcnow()

    for alert, asset in rows:
        sym = asset.symbol.upper()
        price = prices_by_symbol.get(sym)
        if price is None:
            continue

        threshold = float(alert.threshold_price) if isinstance(alert.threshold_price, Decimal) else float(alert.threshold_price)

        triggered = (
            (alert.direction == AlertDirection.above and price >= threshold) or
            (alert.direction == AlertDirection.below and price <= threshold)
        )
        if not triggered:
            continue

        key = _cooldown_key(alert.user_id, alert.id)
        if await r.get(key):
            continue

        text = f"⚠️ {sym}: price={price} crossed {alert.direction} {threshold}"
        ok = False
        if alert.channel == AlertChannel.telegram:
            ok = await send_telegram(text)
        elif alert.channel == AlertChannel.email:
            ok = send_email("user@example.com", f"Alert {sym}", text)

        if ok:
            alert.last_triggered_at = now
            db.add(alert)
            db.commit()
            await r.setex(key, cooldown_sec, "1")
