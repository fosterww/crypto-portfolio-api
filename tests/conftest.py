import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.db.session import Base, get_db
from app.main import app as fastapi_app


os.environ.setdefault("DISABLE_REDIS", "1")

TEST_DATABASE_URL = "sqlite+pysqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    future=True,
)

TestingSessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
        db.commit()
    finally:
        db.close()

fastapi_app.dependency_overrides[get_db] = override_get_db

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
