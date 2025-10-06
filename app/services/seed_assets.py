from sqlalchemy.orm import Session
from app.db.models import Asset

DEFAULT = [
    {"symbol": "BTC", "coingecko_id": "bitcoin"},
    {"symbol": "ETH", "coingecko_id": "ethereum"},
    {"symbol": "SOL", "coingecko_id": "solana"},
]

def seed_assets(db: Session):
    for a in DEFAULT:
        if not db.query(Asset).filter_by(symbol=a["symbol"]).first():
            db.add(Asset(**a))
    db.commit()
