"""周聚合：把「一周」的计划、计划子任务与独立任务收进一个模块。

「一周」= 该周计划 + 计划子任务 + 该周独立任务（``subtask_id`` 为空）。
子任务关联的当日任务视为该子任务的执行实例，由子任务代表，不重复计数。
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tasks import Subtask, Task, WeeklyPlan


def week_start_of(day: date) -> date:
    """某日所在周的周一。"""
    return day - timedelta(days=day.weekday())


def week_end_of(week_start: date) -> date:
    """某周的最后一天（周日）。"""
    return week_start + timedelta(days=6)


@dataclass
class WeekAggregate:
    """一周的计划、计划子任务与独立任务，以及派生计数。"""

    week_start: date
    week_end: date
    plans: list[WeeklyPlan]
    subtasks: list[Subtask]
    tasks: list[Task]

    @property
    def plan_count(self) -> int:
        return len(self.plans)

    @property
    def subtask_count(self) -> int:
        return len(self.subtasks)

    @property
    def task_count(self) -> int:
        return len(self.tasks)

    @property
    def total(self) -> int:
        return len(self.subtasks) + len(self.tasks)

    @property
    def done(self) -> int:
        return sum(1 for s in self.subtasks if s.completed) + sum(
            1 for t in self.tasks if t.completed
        )

    @property
    def completion_rate(self) -> int:
        return round(self.done / self.total * 100) if self.total else 0

    @property
    def daily_counts(self) -> dict[date, int]:
        """每日完成计数（子任务 + 独立任务，按 ``completed_at`` 日期）。"""
        counts: dict[date, int] = defaultdict(int)
        for s in self.subtasks:
            if s.completed and s.completed_at:
                counts[s.completed_at.date()] += 1
        for t in self.tasks:
            if t.completed and t.completed_at:
                counts[t.completed_at.date()] += 1
        return dict(counts)


def fetch_week(db: Session, week_start: date) -> WeekAggregate:
    """一次取齐一周的计划、计划子任务与独立任务，并派生计数。"""
    week_end = week_end_of(week_start)
    plans = list(
        db.scalars(
            select(WeeklyPlan)
            .where(WeeklyPlan.week_start == week_start)
            .order_by(WeeklyPlan.importance.desc(), WeeklyPlan.id)
        ).all()
    )
    plan_ids = [p.id for p in plans]
    subtasks: list[Subtask] = []
    if plan_ids:
        subtasks = list(
            db.scalars(select(Subtask).where(Subtask.plan_id.in_(plan_ids))).all()
        )
    tasks = list(
        db.scalars(
            select(Task)
            .where(
                Task.date >= week_start,
                Task.date <= week_end,
                Task.subtask_id.is_(None),
            )
        ).all()
    )
    return WeekAggregate(week_start, week_end, plans, subtasks, tasks)
