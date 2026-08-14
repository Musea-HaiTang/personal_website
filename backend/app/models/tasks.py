from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.config import now_local
from app.database import Base


class Task(Base):
    """计划任务，预留 user_id 供未来公网登录使用。"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    priority: Mapped[int] = mapped_column(default=2, nullable=False)  # 1 低 / 2 中 / 3 高
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
