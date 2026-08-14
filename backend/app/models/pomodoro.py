import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class PomodoroSession(Base):
    """番茄会话记录，预留 user_id；task_id 供后续绑定计划任务（issue #8）。"""

    __tablename__ = "pomodoro_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local, nullable=False)
    ended_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local, nullable=False)
    focus_seconds: Mapped[int] = mapped_column(Integer, nullable=False)
    task_id: Mapped[int | None] = mapped_column(ForeignKey("tasks.id"), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
