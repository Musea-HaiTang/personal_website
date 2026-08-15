from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.tasks import Subtask, Task, WeeklyPlan


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(Task))
        db.execute(delete(Subtask))
        db.execute(delete(WeeklyPlan))
        db.commit()


def _create_plan(client, title="完成个人网站 P0", week="2026-08-17"):
    resp = client.post(
        "/api/plans",
        json={"title": title, "week_start": week, "importance": 3, "note": "本周重点"},
    )
    assert resp.status_code == 201
    return resp.json()


def test_plan_and_subtask_crud(client):
    plan = _create_plan(client)
    assert plan["importance"] == 3
    assert plan["subtasks"] == []

    resp = client.get("/api/plans", params={"week_start": "2026-08-17"})
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.post(
        f"/api/plans/{plan['id']}/subtasks",
        json={"name": "计划页改版", "note": "左右分栏", "importance": 3},
    )
    assert resp.status_code == 201
    sub = resp.json()
    assert sub["name"] == "计划页改版"

    resp = client.put(f"/api/subtasks/{sub['id']}", json={"completed": True})
    assert resp.json()["completed"] is True
    assert resp.json()["completed_at"] is not None

    detail = client.get(f"/api/plans/{plan['id']}").json()
    assert len(detail["subtasks"]) == 1
    assert detail["subtasks"][0]["completed"] is True

    assert client.delete(f"/api/subtasks/{sub['id']}").status_code == 204
    assert client.get(f"/api/plans/{plan['id']}").json()["subtasks"] == []


def test_plan_delete_cascades_subtasks(client):
    plan = _create_plan(client)
    sub = client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "子任务"}).json()
    assert client.delete(f"/api/plans/{plan['id']}").status_code == 204
    with SessionLocal() as db:
        assert db.get(Subtask, sub["id"]) is None


def test_task_crud(client):
    resp = client.post(
        "/api/tasks",
        json={"title": "写周报", "date": "2026-08-15", "importance": 2, "note": "本周进展"},
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == "写周报"
    assert task["completed"] is False

    resp = client.get("/api/tasks", params={"date": "2026-08-15"})
    assert len(resp.json()) == 1

    resp = client.put(f"/api/tasks/{task['id']}", json={"title": "写月报", "completed": True})
    assert resp.status_code == 200
    assert resp.json()["title"] == "写月报"
    assert resp.json()["completed"] is True
    assert resp.json()["completed_at"] is not None

    assert client.delete(f"/api/tasks/{task['id']}").status_code == 204
    assert client.get("/api/tasks").json() == []


def test_task_filter_by_date(client):
    client.post("/api/tasks", json={"title": "今天", "date": "2026-08-14"})
    client.post("/api/tasks", json={"title": "明天", "date": "2026-08-15"})
    tasks = client.get("/api/tasks", params={"date": "2026-08-15"}).json()
    assert [t["title"] for t in tasks] == ["明天"]


def test_task_complete_syncs_subtask(client):
    plan = _create_plan(client)
    sub = client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "前端联调"}).json()
    task = client.post(
        "/api/tasks",
        json={"title": "前端联调", "date": "2026-08-15", "plan_id": plan["id"], "subtask_id": sub["id"]},
    ).json()
    assert task["plan_title"] == "完成个人网站 P0"
    assert task["subtask_name"] == "前端联调"

    done = client.put(f"/api/tasks/{task['id']}", json={"completed": True}).json()
    assert done["completed"] is True
    assert client.get(f"/api/plans/{plan['id']}").json()["subtasks"][0]["completed"] is True

    reopened = client.put(f"/api/tasks/{task['id']}", json={"completed": False}).json()
    assert reopened["completed"] is False
    assert client.get(f"/api/plans/{plan['id']}").json()["subtasks"][0]["completed"] is False


def test_rollover_task(client):
    task = client.post("/api/tasks", json={"title": "没做完", "date": "2026-08-15"}).json()
    client.put(f"/api/tasks/{task['id']}", json={"completed": True})
    resp = client.post(f"/api/tasks/{task['id']}/rollover")
    assert resp.status_code == 200
    moved = resp.json()
    assert moved["date"] == "2026-08-16"
    assert moved["completed"] is False


def test_export_week(client):
    plan = _create_plan(client)
    client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "计划页改版"})
    done = client.post(f"/api/plans/{plan['id']}/subtasks", json={"name": "后端接口"}).json()
    client.put(f"/api/subtasks/{done['id']}", json={"completed": True})

    resp = client.get("/api/plans/week/export", params={"week_start": "2026-08-17"})
    assert resp.status_code == 200
    body = resp.text
    assert "完成个人网站 P0" in body
    assert "- [ ] 计划页改版" in body
    assert "- [x] 后端接口" in body
    assert "共 2 项，完成 1 项" in body


def test_404_and_validation(client):
    assert client.put("/api/plans/999", json={"title": "x"}).status_code == 404
    assert client.delete("/api/subtasks/999").status_code == 404
    assert client.put("/api/tasks/999", json={"title": "x"}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404
    assert client.post("/api/tasks", json={"title": "", "date": "bad"}).status_code == 422
    assert client.post("/api/plans", json={"title": "x", "week_start": "bad"}).status_code == 422
