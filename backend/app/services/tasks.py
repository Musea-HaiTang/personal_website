from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import now_local
from app.models.tasks import Subtask, Task, WeeklyPlan
from app.schemas.tasks import (
    SubtaskCreate,
    SubtaskUpdate,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    WeeklyPlanCreate,
    WeeklyPlanUpdate,
)


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
    """导出本周计划为 Markdown：按计划列出子任务与完成状态，结尾给完成率。"""
    plans = db.scalars(
        select(WeeklyPlan)
        .where(WeeklyPlan.week_start == week_start)
        .order_by(WeeklyPlan.importance.desc(), WeeklyPlan.id)
    ).all()
    lines = [f"# {week_start} ~ {week_start + timedelta(days=6)} 周计划", ""]
    total = 0
    done = 0
    for plan in plans:
        lines.append(f"## {plan.title}")
        for sub in plan.subtasks:
            total += 1
            if sub.completed:
                done += 1
                when = sub.completed_at.strftime("%m-%d %H:%M") if sub.completed_at else ""
                lines.append(f"- [x] {sub.name}（完成于 {when}）")
            else:
                lines.append(f"- [ ] {sub.name}")
        if not plan.subtasks:
            lines.append("- （还没有子任务）")
        lines.append("")
    rate = f"{done / total * 100:.1f}%" if total else "0%"
    lines.append(f"共 {total} 项，完成 {done} 项，完成率 {rate}")
    return "\n".join(lines)
