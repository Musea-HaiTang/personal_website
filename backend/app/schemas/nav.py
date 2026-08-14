from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class NavCategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    sort_order: int = 0


class NavCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=50)
    sort_order: int | None = None


class NavLinkCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    url: str = Field(min_length=1, max_length=500)
    description: str | None = None
    category_id: int
    is_pinned: bool = False
    sort_order: int = 0


class NavLinkUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=100)
    url: str | None = Field(default=None, min_length=1, max_length=500)
    description: str | None = None
    category_id: int | None = None
    is_pinned: bool | None = None
    sort_order: int | None = None


class NavLinkOut(NavLinkCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class NavCategoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sort_order: int
    created_at: datetime
    links: list[NavLinkOut] = []
