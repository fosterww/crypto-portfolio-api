from tests.conftest import signup_and_login

def test_portfolio_page(client):
    token = signup_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    #create
    r = client.post("/portfolio", json={"name": "Main"}, headers=headers)
    assert r.status_code == 201
    pid = r.json()["id"]
    assert r.json()["name"] == "Main"

    #list
    r = client.get("/portfolio?limit=20&offset=0", headers=headers)
    assert r.status_code == 200
    items = r.json()
    assert isinstance(items, list)
    assert any(p["id"] == pid for p in items)

    #rename
    r = client.patch(f"/portfolio/{pid}", json={"name": "Long-term"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["name"] == "Long-term"

    #get one
    r = client.get(f"/portfolio/{pid}", headers=headers)
    assert r.status_code == 200
    assert r.json()["id"] == pid

    # delete
    r = client.delete(f"/portfolio/{pid}", headers=headers)
    assert r.status_code == 204

    # get after delete -> 404
    r = client.get(f"/portfolio/{pid}", headers=headers)
    assert r.status_code == 404