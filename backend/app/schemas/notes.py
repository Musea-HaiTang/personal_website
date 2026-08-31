import datetime

from pydantic import BaseModel, ConfigDict, Field


class NoteCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    folder: str = Field(default="未分类", max_length=100)
    tags: list[str] = []
    content: str = ""


class FolderCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class NoteListItem(BaseModel):
    """列表项：只含元信息，不含正文（列表页仅展示标题/标签/分类）。"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    folder: str
    title: str
    tags: list[str]
    updated_at: datetime.datetime


class NoteDetail(BaseModel):
    """单条详情：含完整正文（阅读弹窗打开时按 id 获取）。"""

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
    created: list[NoteListItem]
    renamed: list[str]
    errors: list[str]
