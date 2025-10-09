from pydantic import BaseModel, Field, field_serializer, ConfigDict
from decimal import Decimal

class PortfolioCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)

class PortfolioUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)

class PortfolioOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True

class PositionSummaryOut(BaseModel):
    asset_symbol: str | None
    qty: str
    avg_buy_price: str
    price: Decimal
    value: Decimal
    pnl: Decimal

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @field_serializer('price', 'value', 'pnl')
    def ser_decimal(self, v: Decimal, _info):
        return format(v, 'f')

class PortfolioSummaryOut(BaseModel):
    portfolio_id: int
    vs: str
    total_value: float
    total_cost: float
    total_pnl: float
    pnl_pct: float
    positions: list[PositionSummaryOut]