from pydantic import BaseModel, Field
from app.db.models import AlertDirection, AlertChannel
from typing import Annotated
from decimal import Decimal
from typing import Annotated

class AlertCreateIn(BaseModel):
    asset_id: int
    direction: AlertDirection
    threshold_price: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=6)]
    channel: AlertChannel = AlertChannel.telegram
    is_active: bool = True

class AlertUpdate(BaseModel):
    direction: AlertDirection | None = None
    threshold_price: Annotated[Decimal, Field(gt=0, max_digits=18, decimal_places=6)] | None = None
    channel: AlertChannel | None = None
    is_active: bool | None = None

class AlertOut(BaseModel):
    id: int
    user_id: int
    asset_id: int
    direction: AlertDirection
    threshold_price: float
    channel: AlertChannel
    is_active: bool

    class Config:
        from_attributes = True