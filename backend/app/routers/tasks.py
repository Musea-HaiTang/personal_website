from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session

from app.database import get_db
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
from app.services import tasks as tasks_service

router = APIRouter(tags=["tasks"])


@router.get("/api/plans", response_model=list[WeeklyPlanOut])
def list_plans(week_start: date | None = Query(default=None), db: Session = Depends(get_db)):
    return tasks_service.list_plans(db, week_start)


@router.post("/api/plans", response_model=WeeklyPlanOut, status_code=201)
def create_plan(payload: WeeklyPlanCreate, db: Session = Depends(get_db)):
    return tasks_service.create_plan(db, payload)


@router.get("/api/plans/{plan_id}", response_model=WeeklyPlanOut)
def get_plan(plan_id: int, db: Session = Depends(get_db)):
    return tasks_service.plan_or_404(db, plan_id)


@router.put("/api/plans/{plan_id}", response_model=WeeklyPlanOut)
def update_plan(plan_id: int, payload: WeeklyPlanUpdate, db: Session = Depends(get_db)):
    return tasks_service.update_plan(db, plan_id, payload)


@router.delete("/api/plans/{plan_id}", status_code=204)
def delete_plan(plan_id: int, db: Session = Depends(get_db)):
    tasks_service.delete_plan(db, plan_id)


@router.get("/api/plans/week/export", response_class=PlainTextResponse)
def export_week(week_start: date, db: Session = Depends(get_db)):
    return PlainTextResponse(tasks_service.export_week_markdown(db, week_start), media_type="text/markdown; charset=utf-8")


@router.post("/api/plans/{plan_id}/subtasks", response_model=SubtaskOut, status_code=201)
def create_subtask(plan_id: int, payload: SubtaskCreate, db: Session = Depends(get_db)):
    return tasks_service.create_subtask(db, plan_id, payload)


@router.put("/api/subtasks/{subtask_id}", response_model=SubtaskOut)
def update_subtask(subtask_id: int, payload: SubtaskUpdate, db: Session = Depends(get_db)):
    return tasks_service.update_subtask(db, subtask_id, payload)


@router.delete("/api/subtasks/{subtask_id}", status_code=204)
def delete_subtask(subtask_id: int, db: Session = Depends(get_db)):
    tasks_service.delete_subtask(db, subtask_id)


@router.get("/api/tasks", response_model=list[TaskOut])
def list_tasks(task_date: date | None = Query(default=None, alias="date"), db: Session = Depends(get_db)):
    return tasks_service.list_tasks(db, task_date)


@router.post("/api/tasks", response_model=TaskOut, status_code=201)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return tasks_service.create_task(db, payload)


@router.get("/api/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db)):
    return tasks_service.task_to_out(tasks_service.task_or_404(db, task_id))


@router.put("/api/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    return tasks_service.update_task(db, task_id, payload)


@router.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    tasks_service.delete_task(db, task_id)


@router.post("/api/tasks/{task_id}/rollover", response_model=TaskOut)
def rollover_task(task_id: int, new_date: date | None = None, db: Session = Depends(get_db)):
    return tasks_service.rollover_task(db, task_id, new_date)
