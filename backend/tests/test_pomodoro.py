import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.pomodoro import PomodoroSession
from app.models.tasks import Task


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(PomodoroSession))
        db.execute(delete(Task))
        db.commit()


def test_create_session_and_day_summary(client):
    resp = client.post("/api/pomodoro/sessions", json={"focus_seconds": 1500})
    assert resp.status_code == 201
    session = resp.json()
    assert session["focus_seconds"] == 1500
    assert session["task_id"] is None

    resp = client.post("/api/pomodoro/sessions", json={"focus_seconds": 600})
    assert resp.status_code == 201

    summary = client.get("/api/pomodoro/sessions").json()
    assert summary["count"] == 2
    assert summary["total_seconds"] == 2100


def test_day_filter_uses_local_date(client):
    today = datetime.date.today()
    client.post("/api/pomodoro/sessions", json={"focus_seconds": 1500})

    summary = client.get("/api/pomodoro/sessions", params={"day": today.isoformat()}).json()
    assert summary["count"] == 1

    yesterday = (today - datetime.timedelta(days=1)).isoformat()
    summary = client.get("/api/pomodoro/sessions", params={"day": yesterday}).json()
    assert summary["count"] == 0


def test_create_session_validation(client):
    assert client.post("/api/pomodoro/sessions", json={"focus_seconds": 0}).status_code == 422
    assert client.post("/api/pomodoro/sessions", json={"focus_seconds": -5}).status_code == 422


def test_session_can_bind_task(client):
    task = client.post(
        "/api/tasks",
        json={"title": "写周报", "date": datetime.date.today().isoformat(), "importance": 2},
    ).json()

    resp = client.post("/api/pomodoro/sessions", json={"focus_seconds": 1500, "task_id": task["id"]})
    assert resp.status_code == 201
    session = resp.json()
    assert session["task_id"] == task["id"]
    assert session["task_title"] == "写周报"

    summary = client.get("/api/pomodoro/sessions").json()
    assert summary["sessions"][0]["task_title"] == "写周报"


def test_session_rejects_unknown_task(client):
    resp = client.post("/api/pomodoro/sessions", json={"focus_seconds": 1500, "task_id": 99999})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "任务不存在"
