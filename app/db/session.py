from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

if not getattr(settings, "DATABASE_URL", None):
    raise RuntimeError("DATABASE_URL is missing. Set it in Railway Variables")

from sqlalchemy.engine.url import make_url
print("DB URL parsed ->", make_url(settings.DATABASE_URL))
engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
print("RAW DSN ->", repr(getattr(settings, "DATABASE_URL", None)))

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()