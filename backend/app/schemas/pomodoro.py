import datetime

from pydantic import BaseModel, ConfigDict, Field


class PomodoroSessionCreate(BaseModel):
    focus_seconds: int = Field(gt=0, le=24 * 3600)
    task_id: int | None = None


class PomodoroSessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    started_at: datetime.datetime
    ended_at: datetime.datetime
    focus_seconds: int
    task_id: int | None
    task_title: str | None = None


class PomodoroDaySummary(BaseModel):
    count: int
    total_seconds: int
    sessions: list[PomodoroSessionOut]
