from typing import Annotated
from pydantic import BaseModel, Field

class PaginationParams(BaseModel):
    limit: Annotated[int, Field(gt=0, le=100, default=20)]
    offset: Annotated[int, Field(ge=0, default=0)]