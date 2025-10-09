from fastapi import FastAPI
from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.portfolio import router as portfolio_router
from app.api.positions import router as positions_router
from app.api.prices import router as prices_router

app = FastAPI(title="Crypto Portfolio API")
app.include_router(health_router, prefix="/health", tags=["Health"])
app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(portfolio_router, prefix="/portfolio", tags=["portfolio"])
app.include_router(positions_router, prefix="/positions", tags=["positions"])
app.include_router(prices_router, prefix="/prices", tags=["prices"])