from decimal import Decimal
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models import User, Asset, Portfolio, Position
from app.utils.hash import hash_password

def run():
    db: Session = SessionLocal()
    try:
        assets = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana"}
        for sym, cid in assets.items():
            if not db.query(Asset).filter_by(symbol=sym).first():
                db.add(Asset(symbol=sym, coingecko_id=cid))
        db.commit()

        email = "demo@user.io"
        user = db.query(User).filter_by(email=email).first()
        if not user:
            user = User(email=email, password_hash=hash_password("demo1234"))
            db.add(user); db.commit(); db.refresh(user)

        port = db.query(Portfolio).filter_by(user_id=user.id, name="Demo").first()
        if not port:
            port = Portfolio(user_id=user.id, name="Demo")
            db.add(port); db.commit(); db.refresh(port)

        if not db.query(Position).filter_by(portfolio_id=port.id).first():
            btc = db.query(Asset).filter_by(symbol="BTC").first()
            eth = db.query(Asset).filter_by(symbol="ETH").first()
            sol = db.query(Asset).filter_by(symbol="SOL").first()
            db.add(Position(portfolio_id=port.id, asset_id=btc.id, qty=Decimal(0.0), avg_buy_price=Decimal("30000")))
            db.add(Position(portfolio_id=port.id, asset_id=eth.id, qty=Decimal("1.5"),  avg_buy_price=Decimal("1700")))
            db.add(Position(portfolio_id=port.id, asset_id=sol.id, qty=Decimal("10"),   avg_buy_price=Decimal("20")))
            db.commit()
        print("Demo ready: demo@user.io / demo1234")
    finally:
        db.close()

if __name__ == "__main__":
    run()