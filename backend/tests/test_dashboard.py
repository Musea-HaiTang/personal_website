import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.main import app
from app.models.diary import DiaryEntry
from app.models.nav import NavCategory, NavLink
from app.models.pomodoro import PomodoroSession
from app.models.tasks import Subtask, Task, WeeklyPlan
from app.services.markdown_store import diary_store


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        for entry in db.scalars(select(DiaryEntry)).all():
            diary_store.delete(diary_store.path_for(str(entry.date)))
        db.execute(delete(DiaryEntry))
        db.execute(delete(NavLink))
        db.execute(delete(NavCategory))
        db.execute(delete(PomodoroSession))
        db.execute(delete(Task))
        db.execute(delete(Subtask))
        db.execute(delete(WeeklyPlan))
        db.commit()


def test_empty_dashboard(client):
    resp = client.get("/api/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["today_tasks"] == []
    assert data["pomodoro"] == {"count": 0, "total_seconds": 0}
    assert data["recent_diaries"] == []
    assert data["pinned_links"] == []


def test_dashboard_aggregates_four_blocks(client):
    today = datetime.date.today().isoformat()
    tomorrow = (datetime.date.today() + datetime.timedelta(days=1)).isoformat()

    # 今日未完成、今日已完成、明天的任务：首页只出现今日未完成
    client.post("/api/tasks", json={"title": "待办A", "date": today, "importance": 3})
    done = client.post("/api/tasks", json={"title": "已完成", "date": today}).json()
    client.put(f"/api/tasks/{done['id']}", json={"completed": True})
    client.post("/api/tasks", json={"title": "明天的任务", "date": tomorrow})

    # 今日番茄
    client.post("/api/pomodoro/sessions", json={"focus_seconds": 1500})
    client.post("/api/pomodoro/sessions", json={"focus_seconds": 600})

    # 日记按日期倒序
    client.post(
        "/api/diary", json={"date": "2026-08-14", "title": "旧日记", "tags": ["生活"], "content": "第一天"}
    )
    client.post(
        "/api/diary", json={"date": "2026-08-15", "title": "新日记", "tags": ["工作"], "content": "第二天"}
    )

    # 导航：只有置顶链接出现
    cat = client.post("/api/nav/categories", json={"name": "常用"}).json()
    client.post("/api/nav/links", json={"title": "普通", "url": "https://a.com", "category_id": cat["id"]})
    client.post(
        "/api/nav/links",
        json={"title": "置顶", "url": "https://b.com", "is_pinned": True, "category_id": cat["id"]},
    )

    data = client.get("/api/dashboard").json()
    assert [t["title"] for t in data["today_tasks"]] == ["待办A"]
    assert data["pomodoro"] == {"count": 2, "total_seconds": 2100}
    assert [e["title"] for e in data["recent_diaries"]] == ["新日记", "旧日记"]
    assert [l["title"] for l in data["pinned_links"]] == ["置顶"]
