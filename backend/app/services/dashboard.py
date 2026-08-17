import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOCAL_TZ, now_local
from app.models.diary import DiaryEntry
from app.models.nav import NavLink
from app.models.pomodoro import PomodoroSession
from app.models.tasks import Task
from app.schemas.dashboard import DashboardOut, PomodoroSummary
from app.schemas.diary import DiaryOut
from app.schemas.nav import NavLinkOut
from app.services import tags
from app.services.markdown_store import diary_store
from app.services.tasks import task_to_out


def get_dashboard(db: Session) -> DashboardOut:
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
            tags=tags.to_list(entry.tags),
            content=diary_store.read(diary_store.path_for(str(entry.date))),
            updated_at=entry.updated_at,
        )
        for entry in entries
    ]

    links = db.scalars(
        select(NavLink).where(NavLink.is_pinned.is_(True)).order_by(NavLink.sort_order, NavLink.id)
    ).all()

    return DashboardOut(
        today_tasks=[task_to_out(t) for t in tasks],
        pomodoro=PomodoroSummary(count=len(sessions), total_seconds=sum(s.focus_seconds for s in sessions)),
        recent_diaries=diaries,
        pinned_links=[NavLinkOut.model_validate(link) for link in links],
    )
