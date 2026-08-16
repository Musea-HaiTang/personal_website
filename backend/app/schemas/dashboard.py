from pydantic import BaseModel

from app.schemas.diary import DiaryOut
from app.schemas.nav import NavLinkOut
from app.schemas.tasks import TaskOut


class PomodoroSummary(BaseModel):
    count: int
    total_seconds: int


class DashboardOut(BaseModel):
    today_tasks: list[TaskOut]
    pomodoro: PomodoroSummary
    recent_diaries: list[DiaryOut]
    pinned_links: list[NavLinkOut]
