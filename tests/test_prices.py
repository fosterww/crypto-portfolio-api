import json
from tests.conftest import signup_and_login, override_get_db
from sqlalchemy.orm import Session
from app.db.models import Asset
from app.services import coingecko

def fake_get_simple_price(ids, vs_currency="usd"):
    base = {"bitcoin": 50000.0, "ethereum": 3000.0}
    return {i: base.get(i, 0.0) for i in ids}

def seed_assets(client):
    for db in override_get_db():
        assert isinstance(db, Session)
        if not db.query(Asset).filter_by(symbol="BTC").first():
            db.add(Asset(symbol="BTC", coingecko_id="bitcoin"))
        if not db.query(Asset).filter_by(symbol="ETH").first():
            db.add(Asset(symbol="ETH", coingecko_id="ethereum"))
        db.commit()

def test_prices_endpoint(monkeypatch, client):
    seed_assets(client)

    monkeypatch.setattr(coingecko, "get_simple_price", lambda ids, vs_currency="usd": fake_get_simple_price(ids, vs_currency))

    r = client.get("/prices?symbols=BTC,ETH&vs=usd")
    assert r.status_code == 200
    data = r.json()
    assert data["vs"] == "usd"
    assert data["prices"]["BTC"] == 50000.0
    assert data["prices"]["ETH"] == 3000.0
