from datetime import datetime
from decimal import Decimal, InvalidOperation
from sqlalchemy.orm import Session
from app.db.models import Alert, Asset, AlertDirection, AlertChannel, AlertEvent
from app.services.pricing import get_prices_cached
from app.core.cache import get_redis
from app.core.config import settings
from app.services.notifier import send_telegram_global, send_email

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

    symbols = [asset.symbol for _, asset in rows]
    prices_map: dict[str, float] = await get_prices_cached(db, symbols)

    r = await get_redis()
    now = datetime.utcnow()

    for alert, asset in rows:
        price_raw = prices_map.get(asset.symbol)
        if price_raw is None:
            continue

        try:
            price = Decimal(str(price_raw))
        except (InvalidOperation, TypeError):
            continue

        try:
            threshold = Decimal(str(alert.threshold_price))
        except (InvalidOperation, TypeError):
            continue

        cooldown_sec = settings.ALERT_COOLDOWN_SEC or 0
        key = f"alert:{alert.user_id}:{alert.id}:cooldown"
        if cooldown_sec > 0:
            if await r.get(key):
                continue

        if alert.direction == AlertDirection.above:
            crossed = price >= threshold
        elif alert.direction == AlertDirection.below:
            crossed = price <= threshold
        else:
            continue

        prev_side_key = f"alert:{alert.user_id}:{alert.id}:side"
        prev_side = await r.get(prev_side_key)
        current_side = b"above" if price >= threshold else b"below"

        if prev_side is None:
            await r.set(prev_side_key, current_side)

        else:
            if prev_side == current_side:
                pass
            else:
                crossed = True
                await r.set(prev_side_key, current_side)

        if crossed:
            text = f"⚠️ {asset.symbol} price={price} crossed {alert.direction} {threshold}"

            ok = await send_telegram_global(text)
            if alert.channel == AlertChannel.email:
                ok = send_email(alert.user.email, f"Alert {asset.symbol}", text)

            db.add(AlertEvent(alert_id=alert.id, price=price, message=text))

            if ok:
                alert.last_triggered_at = now
                db.add(alert); db.commit()
                if cooldown_sec > 0:
                    await r.setex(key, cooldown_sec, b"1")
            else:
                db.commit()