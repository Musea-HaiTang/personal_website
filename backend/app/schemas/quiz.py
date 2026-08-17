import datetime
import json

from pydantic import BaseModel, ConfigDict, Field


class QuestionCreate(BaseModel):
    category: str = Field(min_length=1, max_length=100)
    no: str = Field(default="", max_length=20)
    type: str = Field(pattern="^(choice|fill)$")
    title: str = Field(min_length=1)
    options: list[str] = []
    accept: list[str] = []
    answer: str = Field(min_length=1, max_length=500)
    code: str | None = None
    reference_answer: str | None = None
    explanation: str = ""
    score: int = Field(default=5, ge=1, le=1000)


class QuestionUpdate(BaseModel):
    category: str | None = Field(default=None, min_length=1, max_length=100)
    no: str | None = Field(default=None, max_length=20)
    type: str | None = Field(default=None, pattern="^(choice|fill)$")
    title: str | None = Field(default=None, min_length=1)
    options: list[str] | None = None
    accept: list[str] | None = None
    answer: str | None = Field(default=None, min_length=1, max_length=500)
    code: str | None = None
    reference_answer: str | None = None
    explanation: str | None = None
    score: int | None = Field(default=None, ge=1, le=1000)


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    category: str
    no: str
    type: str
    title: str
    options: list[str]
    accept: list[str]
    answer: str
    code: str | None
    reference_answer: str | None
    explanation: str
    score: int
    updated_at: datetime.datetime


class ImportItem(BaseModel):
    """导入校验后待确认写入的规范化题目（包含文件级分类）。"""

    category: str
    no: str = ""
    type: str
    title: str
    options: list[str] = []
    accept: list[str] = []
    answer: str
    code: str | None = None
    reference_answer: str | None = None
    explanation: str = ""
    score: int = 5


class ImportPreview(BaseModel):
    category: str
    new: list[str]
    updated: list[str]
    errors: list[str]
    items: list[ImportItem]


class ImportConfirm(BaseModel):
    items: list[ImportItem]


class ImportResult(BaseModel):
    imported: int
    updated: int


def options_from_str(value: str) -> list[str]:
    try:
        parsed = json.loads(value or "[]")
        return parsed if isinstance(parsed, list) else []
    except json.JSONDecodeError:
        return []
