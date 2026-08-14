import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.main import app
from app.models.diary import DiaryEntry
from app.services.diary_files import delete_file


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        entries = db.scalars(select(DiaryEntry)).all()
        for entry in entries:
            delete_file(entry.date)
        db.execute(delete(DiaryEntry))
        db.commit()


def _create(client: TestClient, day: str = "2026-08-14", title: str = "第一篇", tags=None, content: str = "# 你好"):
    return client.post(
        "/api/diary",
        json={"date": day, "title": title, "tags": tags or ["生活"], "content": content},
    )


def test_diary_save_creates_markdown_file(client):
    resp = _create(client)
    assert resp.status_code == 201
    entry = resp.json()
    assert entry["title"] == "第一篇"
    assert entry["tags"] == ["生活"]

    from app.services.diary_files import file_path_for
    day = datetime.date.fromisoformat("2026-08-14")
    assert file_path_for(day).exists()
    assert file_path_for(day).read_text(encoding="utf-8") == "# 你好"


def test_diary_load_and_edit(client):
    entry = _create(client, content="原始内容").json()

    resp = client.put(f"/api/diary/{entry['id']}", json={"title": "改标题", "tags": ["工作", "生活"], "content": "新内容"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "改标题"
    assert data["tags"] == ["工作", "生活"]
    assert data["content"] == "新内容"

    loaded = client.get("/api/diary", params={"day": "2026-08-14"}).json()
    assert loaded[0]["content"] == "新内容"


def test_diary_search(client):
    _create(client, day="2026-08-14", title="工作复盘", tags=["工作"], content="完成导航模块")
    _create(client, day="2026-08-15", title="生活记录", tags=["生活"], content="去公园散步")

    by_date = client.get("/api/diary", params={"day": "2026-08-15"}).json()
    assert [e["title"] for e in by_date] == ["生活记录"]

    by_tag = client.get("/api/diary", params={"tag": "工作"}).json()
    assert [e["title"] for e in by_tag] == ["工作复盘"]

    by_keyword = client.get("/api/diary", params={"q": "公园"}).json()
    assert [e["title"] for e in by_keyword] == ["生活记录"]

    by_title = client.get("/api/diary", params={"q": "复盘"}).json()
    assert [e["title"] for e in by_title] == ["工作复盘"]


def test_diary_delete(client):
    entry = _create(client).json()
    resp = client.delete(f"/api/diary/{entry['id']}")
    assert resp.status_code == 204

    from app.services.diary_files import file_path_for
    day = datetime.date.fromisoformat("2026-08-14")
    assert not file_path_for(day).exists()
    assert client.get("/api/diary").json() == []


def test_diary_duplicate_date_conflict(client):
    _create(client, day="2026-08-14")
    resp = _create(client, day="2026-08-14")
    assert resp.status_code == 409
