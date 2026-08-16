import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import LOCAL_TZ, now_local
from app.database import get_db
from app.models.pomodoro import PomodoroSession
from app.models.tasks import Task
from app.schemas.pomodoro import PomodoroDaySummary, PomodoroSessionCreate, PomodoroSessionOut

router = APIRouter(prefix="/api/pomodoro", tags=["pomodoro"])


@router.get("/sessions", response_model=PomodoroDaySummary)
def list_sessions(day: datetime.date = Query(default_factory=lambda: now_local().date()), db: Session = Depends(get_db)):
    start = datetime.datetime.combine(day, datetime.time.min, tzinfo=LOCAL_TZ)
    end = start + datetime.timedelta(days=1)
    stmt = (
        select(PomodoroSession)
        .where(PomodoroSession.started_at >= start, PomodoroSession.started_at < end)
        .order_by(PomodoroSession.started_at.desc())
    )
    sessions = db.scalars(stmt).all()
    return PomodoroDaySummary(
        count=len(sessions),
        total_seconds=sum(s.focus_seconds for s in sessions),
        sessions=[PomodoroSessionOut.model_validate(s) for s in sessions],
    )


@router.post("/sessions", response_model=PomodoroSessionOut, status_code=201)
def create_session(payload: PomodoroSessionCreate, db: Session = Depends(get_db)):
    if payload.task_id is not None and db.get(Task, payload.task_id) is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    now = now_local()
    started = now - datetime.timedelta(seconds=payload.focus_seconds)
    session = PomodoroSession(
        started_at=started,
        ended_at=now,
        focus_seconds=payload.focus_seconds,
        task_id=payload.task_id,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return PomodoroSessionOut.model_validate(session)
