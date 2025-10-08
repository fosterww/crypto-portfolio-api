from sqlalchemy.orm import Session
from app.db.session import Base
from app.db.models import Asset
from tests.conftest import signup_and_login, override_get_db
import pytest

@pytest.fixture
def asset_id():
    for db in override_get_db():
        assert isinstance(db, Session)
        a = db.query(Asset).filter_by(symbol="BTC").first()
        if a:
            return a.id
        a = Asset(symbol="BTC", coingecko_id="bitcoin")
        db.add(a); db.commit(); db.refresh(a)
        return a.id

def test_positions_crud(client, asset_id):
    
    token = signup_and_login(client, email="pos@example.com")
    headers = {"Authorization": f"Bearer {token}"}

    r = client.post("/portfolio", json={"name": "Spot"}, headers=headers)
    assert r.status_code == 201
    portfolio_id = r.json()["id"]

    payload = {
        "portfolio_id": portfolio_id,
        "asset_id": asset_id,
        "qty": "0.25",
        "avg_buy_price": "30000"
    }
    r = client.post("/positions", json=payload, headers=headers)
    assert r.status_code == 201
    position_id = r.json()["id"]
    assert r.json()["portfolio_id"] == portfolio_id
    assert r.json()["asset_id"] == asset_id

    r = client.get(f"/positions?portfolio_id={portfolio_id}&limit=50&offset=0", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(p["id"] == position_id for p in items)

    r = client.delete(f"/positions/{position_id}", headers=headers)
    assert r.status_code == 204

    r = client.get(f"/positions?portfolio_id={portfolio_id}", headers=headers)
    assert r.status_code == 200
    ids = [p["id"] for p in r.json()]
    assert position_id not in ids
