from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.tasks import Subtask, Task, WeekSummary, WeeklyPlan
from app.services.week import fetch_week, week_start_of


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        with SessionLocal() as db:
            db.execute(delete(Task))
            db.execute(delete(Subtask))
            db.execute(delete(WeeklyPlan))
            db.execute(delete(WeekSummary))
            db.commit()
        yield test_client
        with SessionLocal() as db:
            db.execute(delete(Task))
            db.execute(delete(Subtask))
            db.execute(delete(WeeklyPlan))
            db.execute(delete(WeekSummary))
            db.commit()


def test_week_start_of_monday():
    # 周一即本周起点；周三/周日归本周一；跨年跨月也按周一对齐
    assert week_start_of(date(2026, 8, 17)) == date(2026, 8, 17)
    assert week_start_of(date(2026, 8, 19)) == date(2026, 8, 17)
    assert week_start_of(date(2026, 8, 23)) == date(2026, 8, 17)
    assert week_start_of(date(2026, 1, 1)) == date(2025, 12, 29)


def test_fetch_week_collects_plan_subtask_and_standalone_task(client):
    ws = date(2026, 8, 17)
    plan = client.post(
        "/api/plans", json={"title": "周计划", "week_start": str(ws), "importance": 2}
    ).json()
    sub = client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "子任务A"}).json()
    # 周中的独立任务应被收集
    client.post(
        "/api/tasks", json={"title": "独立任务", "date": str(ws + timedelta(days=2)), "importance": 2}
    )
    # 下周的任务不属于本周
    client.post(
        "/api/tasks", json={"title": "下周任务", "date": str(ws + timedelta(days=7)), "importance": 2}
    )
    # 子任务关联的当日任务由子任务代表，不单独计入 tasks
    client.post(
        "/api/tasks",
        json={
            "title": "子任务执行",
            "date": str(ws + timedelta(days=1)),
            "plan_id": plan["id"],
            "subtask_id": sub["id"],
        },
    )

    with SessionLocal() as db:
        agg = fetch_week(db, ws)
    assert agg.week_start == ws
    assert agg.week_end == ws + timedelta(days=6)
    assert [p.title for p in agg.plans] == ["周计划"]
    assert [s.name for s in agg.subtasks] == ["子任务A"]
    assert [t.title for t in agg.tasks] == ["独立任务"]
    assert agg.plan_count == 1
    assert agg.subtask_count == 1
    assert agg.task_count == 1


def test_fetch_week_completion_rate(client):
    ws = date(2026, 8, 17)
    plan = client.post(
        "/api/plans", json={"title": "P", "week_start": str(ws), "importance": 2}
    ).json()
    sub_done = client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "完成"}).json()
    client.put(f"/api/subtasks/{sub_done['id']}", json={"completed": True})
    client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "未完成"})
    client.post(
        "/api/tasks", json={"title": "独立", "date": str(ws + timedelta(days=1)), "importance": 2}
    )

    with SessionLocal() as db:
        agg = fetch_week(db, ws)
    assert agg.subtask_count == 2
    assert agg.task_count == 1
    assert agg.total == 3
    assert agg.done == 1
    assert agg.completion_rate == round(1 / 3 * 100)
    assert sum(agg.daily_counts.values()) == 1


def test_fetch_week_empty_rate_zero(client):
    ws = date(2026, 8, 17)
    with SessionLocal() as db:
        agg = fetch_week(db, ws)
    assert agg.plans == []
    assert agg.subtasks == []
    assert agg.tasks == []
    assert agg.total == 0
    assert agg.done == 0
    assert agg.completion_rate == 0
    assert agg.daily_counts == {}
