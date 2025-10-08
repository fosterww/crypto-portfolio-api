from pydantic import BaseModel, Field, ConfigDict
from decimal import Decimal
from typing import Annotated

class PositionCreateIn(BaseModel):
    portfolio_id: int
    asset_id: int
    qty: Annotated[Decimal, Field(gt=0, max_digits=38, decimal_places=10)]
    avg_buy_price: Annotated[Decimal, Field(ge=0, max_digits=18, decimal_places=6)]

class PositionOut(BaseModel):
    id: int
    portfolio_id: int
    asset_id: int
    qty: Decimal
    avg_buy_price: Decimal
    model_config = ConfigDict(from_attributes=True)
