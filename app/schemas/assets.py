from pydantic import BaseModel

class PricesOut(BaseModel):
    vs: str
    prices: dict[str, float]