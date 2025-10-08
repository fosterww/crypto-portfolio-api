import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.db.session import Base, get_db
import app.db.models

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture(autouse=True)
def override_dependencies():
    fastapi_app.dependency_overrides[get_db] = override_get_db

    class _FakeRedis:
        def __init__(self): self._store = {}
        async def ping(self): return True
        async def setex(self, key, sec, val): self._store[key] = val
        async def get(self, key): return self._store.get(key)
        async def close(self): pass

    from app.core.cache import get_redis
    async def _fake(): return _FakeRedis()
    fastapi_app.dependency_overrides[get_redis] = _fake

    yield
    fastapi_app.dependency_overrides.clear()

@pytest.fixture
def client():
    from starlette.testclient import TestClient
    with TestClient(fastapi_app) as c:
        yield c

def signup_and_login(client, email="user@example.com", password="secret123"):
    r = client.post("/auth/signup", json={"email": email, "password": password})
    assert r.status_code in (201, 400)
    r = client.post(f"/auth/login?email={email}&password={password}")
    assert r.status_code == 200
    return r.json()["access_token"]
