import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.flash import FlashNote


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(FlashNote))
        db.commit()


def _create(client: TestClient, content: str = "便利贴记灵感"):
    return client.post("/api/flash", json={"content": content})


def test_flash_create_and_list(client):
    resp = _create(client, "今天下午跑了 5 公里")
    assert resp.status_code == 201
    data = resp.json()
    assert data["content"] == "今天下午跑了 5 公里"
    assert data["id"] > 0
    assert data["created_at"]

    listed = client.get("/api/flash").json()
    assert listed[0]["content"] == "今天下午跑了 5 公里"


def test_flash_filter_by_day_and_keyword(client):
    _create(client, "想到了信纸横线的写法")
    _create(client, "周末想去书店")

    by_keyword = client.get("/api/flash", params={"q": "信纸"}).json()
    assert len(by_keyword) == 1
    assert by_keyword[0]["content"] == "想到了信纸横线的写法"

    day = by_keyword[0]["created_at"][:10]
    by_day = client.get("/api/flash", params={"day": day}).json()
    assert len(by_day) == 2  # 两条都是同一天创建的

    other = client.get("/api/flash", params={"day": "1999-01-01"}).json()
    assert other == []


def test_flash_delete(client):
    note = _create(client).json()
    resp = client.delete(f"/api/flash/{note['id']}")
    assert resp.status_code == 204
    assert client.get("/api/flash").json() == []


def test_flash_validation_and_404(client):
    assert client.post("/api/flash", json={"content": ""}).status_code == 422
    assert client.post("/api/flash", json={"content": "x" * 501}).status_code == 422
    assert client.delete("/api/flash/99999").status_code == 404
