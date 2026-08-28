from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.config import now_local
from app.database import Base


class WeeklyPlan(Base):
    """本周计划：一个大方向，含多个子任务；子任务全部完成即计划完成。"""

    __tablename__ = "weekly_plans"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=2, nullable=False)  # 1 低 / 2 中 / 3 高
    week_start: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    subtasks: Mapped[list["Subtask"]] = relationship(
        back_populates="plan", cascade="all, delete-orphan", order_by="Subtask.id"
    )


class Subtask(Base):
    """子任务：属于某个本周计划，带名字、备注、重要度与完成状态。"""

    __tablename__ = "subtasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    plan_id: Mapped[int] = mapped_column(
        ForeignKey("weekly_plans.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    plan: Mapped["WeeklyPlan"] = relationship(back_populates="subtasks")


class Task(Base):
    """今日任务：安排到某天的具体事项，可关联本周计划的子任务，可记录复盘原因。"""

    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    importance: Mapped[int] = mapped_column(Integer, default=2, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    plan_id: Mapped[int | None] = mapped_column(
        ForeignKey("weekly_plans.id", ondelete="SET NULL"), nullable=True, index=True
    )
    subtask_id: Mapped[int | None] = mapped_column(
        ForeignKey("subtasks.id", ondelete="SET NULL"), nullable=True, index=True
    )
    review_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)

    plan: Mapped["WeeklyPlan | None"] = relationship()
    subtask: Mapped["Subtask | None"] = relationship()


class WeekSummary(Base):
    """周总结：按周存储手动填写的收获与下周重点；完成/未完成清单实时派生，不落库。"""

    __tablename__ = "week_summaries"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    week_start: Mapped[date] = mapped_column(Date, nullable=False, unique=True, index=True)
    reflection: Mapped[str | None] = mapped_column(Text, nullable=True)
    next_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=now_local, onupdate=now_local)
    user_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
