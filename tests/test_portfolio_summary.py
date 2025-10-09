from tests.conftest import signup_and_login, override_get_db
from sqlalchemy.orm import Session
from app.db.models import Asset, Portfolio, Position
from decimal import Decimal
from app.services import coingecko

def fake_get_simple_price(ids, vs_currency="usd"):
    return {"bitcoin": 50000.0, "ethereum": 3000.0}

def seed_assets_and_positions(client):
    for db in override_get_db():
        assert isinstance(db, Session)
        btc = db.query(Asset).filter_by(symbol="BTC").first()
        eth = db.query(Asset).filter_by(symbol="ETH").first()
        if not btc:
            btc = Asset(symbol="BTC", coingecko_id="bitcoin"); db.add(btc); db.commit(); db.refresh(btc)
        if not eth:
            eth = Asset(symbol="ETH", coingecko_id="ethereum"); db.add(eth); db.commit(); db.refresh(eth)
        port = Portfolio(user_id=1, name="Test")
        db.add(port); db.commit(); db.refresh(port)
        db.add(Position(portfolio_id=port.id, asset_id=btc.id, qty=Decimal("0.1"), avg_buy_price=Decimal("30000")))
        db.add(Position(portfolio_id=port.id, asset_id=eth.id, qty=Decimal("2"), avg_buy_price=Decimal("1500")))
        db.commit()
        return port.id

def test_portfolio_summary(monkeypatch, client):
    token = signup_and_login(client, email="sum@example.com")
    headers = {"Authorization": f"Bearer {token}"}


    monkeypatch.setattr(coingecko, "get_simple_price", lambda ids, vs_currency="usd": fake_get_simple_price(ids, vs_currency))

    pid = seed_assets_and_positions(client)

    r = client.get(f"/portfolio/{pid}/summary?vs=usd", headers=headers)
    assert r.status_code == 200
    data = r.json()
    assert round(data["total_value"], 2) == 11000.00
    assert round(data["total_cost"], 2) == 6000.00
    assert round(data["total_pnl"], 2) == 5000.00
    assert round(data["pnl_pct"], 2) == 83.33
