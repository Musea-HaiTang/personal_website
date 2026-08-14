import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: datetime.date
    priority: int = Field(default=2, ge=1, le=3)
    note: str | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    date: datetime.date | None = None
    priority: int | None = Field(default=None, ge=1, le=3)
    note: str | None = None
    completed: bool | None = None


class TaskOut(TaskCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    completed: bool
    created_at: datetime.datetime
