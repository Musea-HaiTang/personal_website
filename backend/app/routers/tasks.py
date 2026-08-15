from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.config import now_local
from app.database import get_db
from app.models.tasks import Subtask, Task, WeeklyPlan
from app.schemas.tasks import (
    SubtaskCreate,
    SubtaskOut,
    SubtaskUpdate,
    TaskCreate,
    TaskOut,
    TaskUpdate,
    WeeklyPlanCreate,
    WeeklyPlanOut,
    WeeklyPlanUpdate,
)

router = APIRouter(tags=["tasks"])


def _plan_or_404(db: Session, plan_id: int) -> WeeklyPlan:
    plan = db.get(WeeklyPlan, plan_id)
    if plan is None:
        raise HTTPException(status_code=404, detail="计划不存在")
    return plan


def _subtask_or_404(db: Session, subtask_id: int) -> Subtask:
    subtask = db.get(Subtask, subtask_id)
    if subtask is None:
        raise HTTPException(status_code=404, detail="子任务不存在")
    return subtask


def _task_or_404(db: Session, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task


def _sync_subtask_completion(subtask: Subtask, completed: bool) -> None:
    subtask.completed = completed
    subtask.completed_at = now_local() if completed else None


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


# ---------------- 本周计划 ----------------


@router.get("/api/plans", response_model=list[WeeklyPlanOut])
def list_plans(week_start: date | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(WeeklyPlan)
    if week_start is not None:
        stmt = stmt.where(WeeklyPlan.week_start == week_start)
    stmt = stmt.order_by(WeeklyPlan.importance.desc(), WeeklyPlan.id)
    return db.scalars(stmt).all()


@router.post("/api/plans", response_model=WeeklyPlanOut, status_code=201)
def create_plan(payload: WeeklyPlanCreate, db: Session = Depends(get_db)):
    plan = WeeklyPlan(**payload.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return plan


@router.get("/api/plans/{plan_id}", response_model=WeeklyPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    return _plan_or_404(db, plan_id)


@router.put("/api/plans/{plan_id}", response_model=WeeklyPlanOut)
def update_plan(plan_id: int, payload: WeeklyPlanUpdate, db: Session = Depends(get_db)):
    plan = _plan_or_404(db, plan_id)
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(plan, key, value)
    db.commit()
    db.refresh(plan)
    return plan


@router.delete("/api/plans/{plan_id}", status_code=204)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    plan = _plan_or_404(db, plan_id)
    db.delete(plan)
    db.commit()


@router.get("/api/plans/week/export", response_class=PlainTextResponse)
def export_week(week_start: date, db: Session = Depends(get_db)):
    plans = db.scalars(
        select(WeeklyPlan).where(WeeklyPlan.week_start == week_start).order_by(WeeklyPlan.importance.desc(), WeeklyPlan.id)
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
    return PlainTextResponse("\n".join(lines), media_type="text/markdown; charset=utf-8")


# ---------------- 子任务 ----------------


@router.post("/api/plans/{plan_id}/subtasks", response_model=SubtaskOut, status_code=201)
def create_subtask(plan_id: int, payload: SubtaskCreate, db: Session = Depends(get_db)):
    _plan_or_404(db, plan_id)
    subtask = Subtask(plan_id=plan_id, **payload.model_dump())
    db.add(subtask)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.put("/api/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(subtask_id: int, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    subtask = _subtask_or_404(db, subtask_id)
    data = payload.model_dump(exclude_unset=True)
    if "completed" in data:
        _sync_subtask_completion(subtask, bool(data.pop("completed")))
    for key, value in data.items():
        setattr(subtask, key, value)
    db.commit()
    db.refresh(subtask)
    return subtask


@router.delete("/api/subtasks/{subtask_id}", status_code=204)
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    subtask = _subtask_or_404(db, subtask_id)
    db.execute(update(Task).where(Task.subtask_id == subtask_id).values(subtask_id=None))
    db.delete(subtask)
    db.commit()


# ---------------- 今日任务 ----------------


@router.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(task_date: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    stmt = select(Task)
    if task_date is not None:
        stmt = stmt.where(Task.date == task_date)
    stmt = stmt.order_by(Task.completed.asc(), Task.importance.desc(), Task.id)
    tasks = db.scalars(stmt).all()
    return [_task_out(t) for t in tasks]


@router.post("/api/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    data = payload.model_dump()
    if data.get("subtask_id") is not None:
        subtask = _subtask_or_404(db, data["subtask_id"])
        data["plan_id"] = subtask.plan_id
    elif data.get("plan_id") is not None:
        _plan_or_404(db, data["plan_id"])
    task = Task(**data)
    db.add(task)
    db.commit()
    db.refresh(task)
    return _task_out(task)


@router.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return _task_out(_task_or_404(db, task_id))


@router.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    task = _task_or_404(db, task_id)
    data = payload.model_dump(exclude_unset=True)
    if "completed" in data:
        completed = bool(data.pop("completed"))
        task.completed = completed
        task.completed_at = now_local() if completed else None
        if task.subtask_id is not None:
            _sync_subtask_completion(_subtask_or_404(db, task.subtask_id), completed)
    if "subtask_id" in data:
        if data["subtask_id"] is None:
            data["plan_id"] = None
        else:
            subtask = _subtask_or_404(db, data["subtask_id"])
            data["plan_id"] = subtask.plan_id
    for key, value in data.items():
        setattr(task, key, value)
    db.commit()
    db.refresh(task)
    return _task_out(task)


@router.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = _task_or_404(db, task_id)
    db.delete(task)
    db.commit()


@router.post("/api/tasks/{task_id}/rollover", response_model=TaskOut)
def rollover_task(task_id: int, new_date: date | None = None, db: Session = Depends(get_db)):
    task = _task_or_404(db, task_id)
    task.date = new_date if new_date is not None else task.date + timedelta(days=1)
    task.completed = False
    task.completed_at = None
    if task.subtask_id is not None:
        _sync_subtask_completion(_subtask_or_404(db, task.subtask_id), False)
    db.commit()
    db.refresh(task)
    return _task_out(task)
