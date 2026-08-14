import datetime

from pydantic import BaseModel, ConfigDict, Field


class DiaryCreate(BaseModel):
    date: datetime.date
    title: str = Field(min_length=1, max_length=200)
    tags: list[str] = []
    content: str = ""


class DiaryUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    tags: list[str] | None = None
    content: str | None = None


class DiaryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: datetime.date
    title: str
    tags: list[str]
    content: str
    updated_at: datetime.datetime
