import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubtaskCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    note: str | None = None
    importance: int = Field(default=2, ge=1, le=3)


class SubtaskUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    note: str | None = None
    importance: int | None = Field(default=None, ge=1, le=3)
    completed: bool | None = None


class SubtaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    name: str
    note: str | None
    importance: int
    completed: bool
    completed_at: datetime.datetime | None
    created_at: datetime.datetime


class WeeklyPlanCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    week_start: datetime.date
    importance: int = Field(default=2, ge=1, le=3)
    note: str | None = None


class WeeklyPlanUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    week_start: datetime.date | None = None
    importance: int | None = Field(default=None, ge=1, le=3)
    note: str | None = None


class WeeklyPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    note: str | None
    importance: int
    week_start: datetime.date
    subtasks: list[SubtaskOut] = []
    created_at: datetime.datetime


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    date: datetime.date
    importance: int = Field(default=2, ge=1, le=3)
    note: str | None = None
    plan_id: int | None = None
    subtask_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    date: datetime.date | None = None
    importance: int | None = Field(default=None, ge=1, le=3)
    note: str | None = None
    completed: bool | None = None
    plan_id: int | None = None
    subtask_id: int | None = None
    review_note: str | None = None


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    note: str | None
    importance: int
    date: datetime.date
    completed: bool
    completed_at: datetime.datetime | None
    plan_id: int | None
    subtask_id: int | None
    review_note: str | None
    plan_title: str | None = None
    subtask_name: str | None = None
    created_at: datetime.datetime


class DailyCount(BaseModel):
    date: datetime.date
    count: int


class WeeklyStatsOut(BaseModel):
    week_start: datetime.date
    completion_rate: int
    plan_count: int
    subtask_count: int
    task_count: int
    daily_counts: list[DailyCount]


class StatsOut(BaseModel):
    weeks: list[WeeklyStatsOut]


class SummaryItem(BaseModel):
    title: str
    kind: str  # 'task' | 'subtask'
    completed_at: datetime.datetime | None = None


class WeekSummaryOut(BaseModel):
    week_start: datetime.date
    done: list[SummaryItem] = []
    undone: list[SummaryItem] = []
    reflection: str | None = None
    next_plan: str | None = None
    updated_at: datetime.datetime | None = None


class WeekSummaryUpdate(BaseModel):
    reflection: str | None = None
    next_plan: str | None = None
