from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.tasks import Task


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(Task))
        db.commit()


def test_task_crud(client):
    resp = client.post(
        "/api/tasks",
        json={"title": "写周报", "date": "2026-08-15", "priority": 2, "note": "本周进展"},
    )
    assert resp.status_code == 201
    task = resp.json()
    assert task["title"] == "写周报"
    assert task["completed"] is False

    resp = client.get("/api/tasks")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.put(f"/api/tasks/{task['id']}", json={"title": "写月报", "completed": True})
    assert resp.status_code == 200
    assert resp.json()["title"] == "写月报"
    assert resp.json()["completed"] is True

    resp = client.delete(f"/api/tasks/{task['id']}")
    assert resp.status_code == 204
    assert client.get("/api/tasks").json() == []


def test_task_filter_by_date(client):
    client.post("/api/tasks", json={"title": "今天", "date": "2026-08-14"})
    client.post("/api/tasks", json={"title": "明天", "date": "2026-08-15"})

    resp = client.get("/api/tasks", params={"date": "2026-08-15"})
    assert resp.status_code == 200
    tasks = resp.json()
    assert [t["title"] for t in tasks] == ["明天"]


def test_task_toggle_completed(client):
    task = client.post("/api/tasks", json={"title": "学习", "date": "2026-08-14"}).json()

    resp = client.put(f"/api/tasks/{task['id']}", json={"completed": True})
    assert resp.json()["completed"] is True
    resp = client.put(f"/api/tasks/{task['id']}", json={"completed": False})
    assert resp.json()["completed"] is False


def test_task_incomplete_first(client):
    done = client.post("/api/tasks", json={"title": "已完成任务", "date": "2026-08-14"}).json()
    client.put(f"/api/tasks/{done['id']}", json={"completed": True})
    client.post("/api/tasks", json={"title": "未完成任务", "date": "2026-08-14"})

    tasks = client.get("/api/tasks").json()
    assert [t["title"] for t in tasks] == ["未完成任务", "已完成任务"]


def test_task_404_and_validation(client):
    assert client.put("/api/tasks/999", json={"title": "x"}).status_code == 404
    assert client.delete("/api/tasks/999").status_code == 404
    assert client.post("/api/tasks", json={"title": "", "date": "bad"}).status_code == 422
