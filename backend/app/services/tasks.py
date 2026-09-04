from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import now_local
from app.models.tasks import Subtask, Task, WeeklyPlan
from app.models.tasks import WeekSummary
from app.schemas.tasks import (
    DailyCount,
    SummaryItem,
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    WeeklyPlanCreate,
    WeeklyPlanUpdate,
    WeeklyStatsOut,
    WeekSummaryOut,
    WeekSummaryUpdate,
)
from app.services.week import fetch_week, week_start_of


def plan_or_404(db: Session, plan_id: int) -> WeeklyPlan:
    plan = db.get(WeeklyPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="计划不存在")
    return plan


def subtask_or_404(db: Session, subtask_id: int) -> Subtask:
    subtask = db.get(Subtask, subtask_id)
    if subtask is None:
        raise HTTPException(status_code=404, detail="子任务不存在")
    return subtask


def task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def sync_subtask_completion(subtask: Subtask, completed: bool) -> None:
    subtask.completed = completed
    subtask.completed_at = now_local() if completed else None


def task_to_out(task: Task) -> TaskOut:
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


def list_plans(db: Session, week_start: date | None) -> list[WeeklyPlan]:
    stmt = select(WeeklyPlan)
    if week_start is not None:
        stmt = stmt.where(WeeklyPlan.week_start == week_start)
    stmt = stmt.order_by(WeeklyPlan.importance.desc(), WeeklyPlan.id)
    return db.scalars(stmt).all()


def create_plan(db: Session, payload: WeeklyPlanCreate) -> WeeklyPlan:
    plan = WeeklyPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


def update_plan(db: Session, plan_id: int, payload: WeeklyPlanUpdate) -> WeeklyPlan:
    plan = plan_or_404(db, plan_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


def delete_plan(db: Session, plan_id: int) -> None:
    plan = plan_or_404(db, plan_id)
    db.delete(plan)
    db.commit()


def create_subtask(db: Session, plan_id: int, payload: SubtaskCreate) -> Subtask:
    plan_or_404(db, plan_id)
    subtask = Subtask(plan_id=plan_id, **payload.model_dump())
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


def update_subtask(db: Session, subtask_id: int, payload: SubtaskUpdate) -> Subtask:
    subtask = subtask_or_404(db, subtask_id)
    data = payload.model_dump(exclude_unset=True)
    if "completed" in data:
        sync_subtask_completion(subtask, bool(data.pop("completed")))
    for key, value in data.items():
        setattr(subtask, key, value)
    db.commit()
    db.refresh(subtask)
    return subtask


def delete_subtask(db: Session, subtask_id: int) -> None:
    subtask = subtask_or_404(db, subtask_id)
    db.execute(update(Task).where(Task.subtask_id == subtask_id).values(subtask_id=None))
    db.delete(subtask)
    db.commit()


def list_tasks(db: Session, task_date: date | None) -> list[TaskOut]:
    stmt = select(Task)
    if task_date is not None:
        stmt = stmt.where(Task.date == task_date)
    stmt = stmt.order_by(Task.completed.asc(), Task.importance.desc(), Task.id)
    return [task_to_out(t) for t in db.scalars(stmt).all()]


def create_task(db: Session, payload: TaskCreate) -> TaskOut:
    data = payload.model_dump()
    if data.get("subtask_id") is not None:
        subtask = subtask_or_404(db, data["subtask_id"])
        data["plan_id"] = subtask.plan_id
    elif data.get("plan_id") is not None:
        plan_or_404(db, data["plan_id"])
    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


def update_task(db: Session, task_id: int, payload: TaskUpdate) -> TaskOut:
    task = task_or_404(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    if "completed" in data:
        completed = bool(data.pop("completed"))
        task.completed = completed
        task.completed_at = now_local() if completed else None
        if task.subtask_id is not None:
            sync_subtask_completion(subtask_or_404(db, task.subtask_id), completed)
    if "subtask_id" in data:
        if data["subtask_id"] is None:
            data["plan_id"] = None
        else:
            subtask = subtask_or_404(db, data["subtask_id"])
            data["plan_id"] = subtask.plan_id
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


def delete_task(db: Session, task_id: int) -> None:
    task = task_or_404(db, task_id)
    db.delete(task)
    db.commit()


def rollover_task(db: Session, task_id: int, new_date: date | None = None) -> TaskOut:
    task = task_or_404(db, task_id)
    task.date = new_date if new_date is not None else task.date + timedelta(days=1)
    task.completed = False
    task.completed_at = None
    if task.subtask_id is not None:
        sync_subtask_completion(subtask_or_404(db, task.subtask_id), False)
    db.commit()
    db.refresh(task)
    return task_to_out(task)


def export_week_markdown(db: Session, week_start: date) -> str:
    """导出本周计划为 Markdown：按计划列出子任务与完成状态，结尾给完成率（含独立任务口径）。"""
    agg = fetch_week(db, week_start)
    lines = [f"# {agg.week_start} ~ {agg.week_end} 周计划", ""]
    for plan in agg.plans:
        lines.append(f"## {plan.title}")
        subs = [s for s in agg.subtasks if s.plan_id == plan.id]
        for sub in subs:
            if sub.completed:
                when = sub.completed_at.strftime("%m-%d %H:%M") if sub.completed_at else ""
                lines.append(f"- [x] {sub.name}（完成于 {when}）")
            else:
                lines.append(f"- [ ] {sub.name}")
        if not subs:
            lines.append("- （还没有子任务）")
        lines.append("")
    lines.append(f"共 {agg.total} 项，完成 {agg.done} 项，完成率 {agg.completion_rate}%")
    return "\n".join(lines)


def weekly_stats(db: Session, weeks: int) -> list[WeeklyStatsOut]:
    """近 N 周计划统计：完成率 / 计划数 / 子任务数 / 任务数 + 每日完成计数（供热力图）。"""
    end_week = week_start_of(now_local().date())
    starts = [end_week - timedelta(weeks=(weeks - 1 - i)) for i in range(weeks)]
    result: list[WeeklyStatsOut] = []
    for ws in starts:
        agg = fetch_week(db, ws)
        counts = agg.daily_counts
        daily = [
            DailyCount(date=ws + timedelta(days=d), count=counts.get(ws + timedelta(days=d), 0))
            for d in range(7)
        ]
        result.append(
            WeeklyStatsOut(
                week_start=ws,
                completion_rate=agg.completion_rate,
                plan_count=agg.plan_count,
                subtask_count=agg.subtask_count,
                task_count=agg.task_count,
                daily_counts=daily,
            )
        )
    return result


def get_week_summary(db: Session, week_start: date) -> WeekSummaryOut:
    agg = fetch_week(db, week_start)
    done: list[SummaryItem] = []
    undone: list[SummaryItem] = []
    for t in agg.tasks:
        item = SummaryItem(title=t.title, kind="task", completed_at=t.completed_at)
        (done if t.completed else undone).append(item)
    for s in agg.subtasks:
        item = SummaryItem(title=s.name, kind="subtask", completed_at=s.completed_at)
        (done if s.completed else undone).append(item)
    summary = db.scalars(
        select(WeekSummary).where(WeekSummary.week_start == week_start)
    ).first()
    return WeekSummaryOut(
        week_start=week_start,
        done=done,
        undone=undone,
        reflection=summary.reflection if summary else None,
        next_plan=summary.next_plan if summary else None,
        updated_at=summary.updated_at if summary else None,
    )


def put_week_summary(db: Session, week_start: date, payload: WeekSummaryUpdate) -> WeekSummaryOut:
    summary = db.scalars(
        select(WeekSummary).where(WeekSummary.week_start == week_start)
    ).first()
    if summary is None:
        summary = WeekSummary(
            week_start=week_start, reflection=payload.reflection, next_plan=payload.next_plan
        )
        db.add(summary)
    else:
        if payload.reflection is not None:
            summary.reflection = payload.reflection
        if payload.next_plan is not None:
            summary.next_plan = payload.next_plan
    db.commit()
    db.refresh(summary)
    return get_week_summary(db, week_start)
