from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.core.cache import get_redis
from app.services.seed_assets import seed_assets

router = APIRouter()

@router.get("/ping")
def ping():
    return {"status": "ok"}

@router.get("/db")
def db_health(db: Session = Depends(get_db)):
    return {"db": "ok"}

@router.get("/redis")
async def redis_health(r = Depends(get_redis)):
    pong = await r.ping()
    return {"redis": "ok" if pong else "error"}

@router.get("/cache-test")
async def cache_test(r = Depends(get_redis)):
    await r.setex("health:key", 60, "alive")
    val = await r.get("health:key")
    return {"value": val.decode() if val else None}

@router.post("/seed")
def seed(db: Session = Depends(get_db)):
    seed_assets(db)
    return {"ok": True}