from tests.conftest import signup_and_login, override_get_db

def test_cannot_access_other_user_portfolio(client):
    # u1 создаёт портфель
    t1 = signup_and_login(client, email="u1@x.com")
    headers1 = {"Authorization": f"Bearer {t1}"}
    r = client.post("/portfolio", json={"name":"U1"}, headers=headers1)
    pid = r.json()["id"]

    # u2 пытается прочитать u1
    t2 = signup_and_login(client, email="u2@x.com")
    headers2 = {"Authorization": f"Bearer {t2}"}
    r = client.get(f"/portfolio/{pid}", headers=headers2)
    assert r.status_code == 404

def test_position_validation(client):
    t = signup_and_login(client, email="val@x.com")
    h = {"Authorization": f"Bearer {t}"}
    # создаём портфель
    r = client.post("/portfolio", json={"name":"Val"}, headers=h)
    pid = r.json()["id"]
    # qty <= 0 -> 422
    r = client.post("/positions", json={
        "portfolio_id": pid, "asset_id": 9999, "qty": "0", "avg_buy_price": "1"
    }, headers=h)
    assert r.status_code in (404, 422)
