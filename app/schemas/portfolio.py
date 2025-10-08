from pydantic import BaseModel, Field

class PortfolioCreateIn(BaseModel):
    name: str = Field(min_length=1, max_length=128)

class PortfolioUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=128)

class PortfolioOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True