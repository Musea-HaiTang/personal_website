import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    folder: str = Field(default="未分类", max_length=100)
    tags: list[str] = []
    content: str = ""


class NoteUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    folder: str | None = Field(default=None, max_length=100)
    tags: list[str] | None = None
    content: str | None = None


class NoteOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    folder: str
    title: str
    tags: list[str]
    content: str
    updated_at: datetime.datetime


class FolderOut(BaseModel):
    folder: str
    count: int


class ImportResult(BaseModel):
    created: list[NoteOut]
    renamed: list[str]
    errors: list[str]
