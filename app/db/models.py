from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, DateTime, ForeignKey, Numeric, UniqueConstraint, Index
from datetime import datetime
from app.db.session import Base
from sqlalchemy import Enum as SAEnum, Boolean
import enum

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolios = relationship("Portfolio", back_populates="user")

class Asset(Base):
    __tablename__ = "assets"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    coingecko_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)

class Portfolio(Base):
    __tablename__ = "portfolios"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)

    user = relationship("User", back_populates="portfolios")
    positions = relationship("Position", back_populates="portfolio", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_unique_portfolio_per_user_name", "user_id", "name", unique=True),
    )

class Position(Base):
    __tablename__ = "positions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    portfolio_id: Mapped[int] = mapped_column(ForeignKey("portfolios.id"), index=True)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True)
    qty: Mapped[Numeric] = mapped_column(Numeric(38, 10), nullable=False, default=0)
    avg_buy_price: Mapped[Numeric] = mapped_column(Numeric(18, 6), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    portfolio = relationship("Portfolio", back_populates="positions")

class AlertDirection(str, enum.Enum):
    above = "above"
    below = "below"

class AlertChannel(str, enum.Enum):
    telegram = "telegram"
    email = "email"

class Alert(Base):
    __tablename__ = "alerts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    direction: Mapped[AlertDirection] = mapped_column(SAEnum(AlertDirection), nullable=False)
    threshold_price: Mapped[Numeric] = mapped_column(Numeric(18, 6), nullable=False)
    channel: Mapped[AlertChannel] = mapped_column(SAEnum(AlertChannel), nullable=False, default=AlertChannel.telegram)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)