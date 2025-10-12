from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
import httpx, asyncio
from app.db.session import get_db
from app.core.cache import get_redis
from app.core.config import settings

router = APIRouter()

@router.get("/status")
async def status(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False

    try:
        r = await get_redis()
        redis_ok = bool(await r.ping())
    except Exception:
        redis_ok = False

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get("https://api.coingecko.com/api/v3/ping")
            cg_ok = resp.status_code == 200
    except Exception:
        cg_ok = False
        
    tg_cfg = bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID)

    return {
        "database": db_ok,
        "redis": redis_ok,
        "coingecko": cg_ok,
        "telegram_configured": tg_cfg,
        "scheduler": True
    }
