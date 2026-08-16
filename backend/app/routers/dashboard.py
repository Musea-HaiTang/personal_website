import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOCAL_TZ, now_local
from app.database import get_db
from app.models.diary import DiaryEntry
from app.models.nav import NavLink
from app.models.pomodoro import PomodoroSession
from app.models.tasks import Task
from app.schemas.dashboard import DashboardOut, PomodoroSummary
from app.schemas.diary import DiaryOut
from app.schemas.nav import NavLinkOut
from app.schemas.tasks import TaskOut
from app.services.diary_files import read_content

router = APIRouter(prefix="/api", tags=["dashboard"])


def _tags_to_list(tags_str: str) -> list[str]:
    return [tag for tag in (tags_str or "").split(",") if tag.strip()]


def _task_out(task: Task) -> TaskOut:
    return TaskOut.model_construct(
        id=task.id,
        title=task.title,
        note=task.note,
        importance=task.importance,
        date=task.date,
        completed=task.completed,
        completed_at=task.completed_at,
        plan_id=task.plan_id,
        subtask_id=task.subtask_id,
        review_note=task.review_note,
        plan_title=task.plan.title if task.plan else None,
        subtask_name=task.subtask.name if task.subtask else None,
        created_at=task.created_at,
    )


@router.get("/dashboard", response_model=DashboardOut)
def get_dashboard(db: Session = Depends(get_db)):
    """一次返回聚合首页四块数据：今日未完成任务、今日专注统计、最近日记、置顶导航。"""
    today = now_local().date()

    tasks = db.scalars(
        select(Task)
        .where(Task.date == today, Task.completed.is_(False))
        .order_by(Task.importance.desc(), Task.id)
    ).all()

    start = datetime.datetime.combine(today, datetime.time.min, tzinfo=LOCAL_TZ)
    end = start + datetime.timedelta(days=1)
    sessions = db.scalars(
        select(PomodoroSession).where(PomodoroSession.started_at >= start, PomodoroSession.started_at < end)
    ).all()

    entries = db.scalars(select(DiaryEntry).order_by(DiaryEntry.date.desc()).limit(5)).all()
    diaries = [
        DiaryOut(
            id=entry.id,
            date=entry.date,
            title=entry.title,
            tags=_tags_to_list(entry.tags),
            content=read_content(entry.date),
            updated_at=entry.updated_at,
        )
        for entry in entries
    ]

    links = db.scalars(
        select(NavLink).where(NavLink.is_pinned.is_(True)).order_by(NavLink.sort_order, NavLink.id)
    ).all()

    return DashboardOut(
        today_tasks=[_task_out(t) for t in tasks],
        pomodoro=PomodoroSummary(count=len(sessions), total_seconds=sum(s.focus_seconds for s in sessions)),
        recent_diaries=diaries,
        pinned_links=[NavLinkOut.model_validate(link) for link in links],
    )
