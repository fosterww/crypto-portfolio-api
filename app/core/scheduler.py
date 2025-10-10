from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.alerts import process_alerts

scheduler: AsyncIOScheduler | None = None

def start_scheduler():
    global scheduler
    if scheduler:
        return scheduler
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(run_alerts_job, IntervalTrigger(minutes=1), id="alerts-check", replace_existing=True)
    scheduler.start()
    return scheduler

async def run_alerts_job():
    db = SessionLocal()
    try:
        await process_alerts(db)
    finally:
        db.close()

def shutdown_scheduler():
    global scheduler
    if scheduler:
        scheduler.shutdown(wait=False)
        scheduler = None