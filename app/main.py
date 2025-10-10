from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.portfolio import router as portfolio_router
from app.api.positions import router as positions_router
from app.api.prices import router as prices_router
from app.api.alerts import router as alerts_router
from app.core.scheduler import start_scheduler, shutdown_scheduler

app = FastAPI(title="Crypto Portfolio API")
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(positions_router, prefix="/positions", tags=["positions"])
app.include_router(prices_router, prefix="/prices", tags=["prices"])
app.include_router(alerts_router, prefix="/alerts", tags=["alerts"])

@app.lifespan("startup")
async def on_startup():
    start_scheduler()

@app.lifespan("shutdown")
async def on_shutdown():
    shutdown_scheduler()