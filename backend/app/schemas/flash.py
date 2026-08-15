import datetime

from pydantic import BaseModel, ConfigDict, Field


class FlashCreate(BaseModel):
    content: str = Field(min_length=1, max_length=500)


class FlashOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    content: str
    created_at: datetime.datetime
