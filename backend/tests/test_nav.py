import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from app.database import SessionLocal
from app.main import app
from app.models.nav import NavCategory, NavLink


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(NavLink))
        db.execute(delete(NavCategory))
        db.commit()


def _create_category(client: TestClient, name: str = "开发", sort_order: int = 0):
    resp = client.post("/api/nav/categories", json={"name": name, "sort_order": sort_order})
    assert resp.status_code == 201
    return resp.json()


def test_category_crud(client):
    category = _create_category(client)
    category_id = category["id"]

    resp = client.get("/api/nav/categories")
    assert resp.status_code == 200
    assert [c["name"] for c in resp.json()] == ["开发"]

    resp = client.put(f"/api/nav/categories/{category_id}", json={"name": "工具"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "工具"

    resp = client.delete(f"/api/nav/categories/{category_id}")
    assert resp.status_code == 204
    assert client.get("/api/nav/categories").json() == []


def test_link_crud(client):
    category = _create_category(client)

    resp = client.post(
        "/api/nav/links",
        json={
            "title": "GitHub",
            "url": "https://github.com",
            "description": "代码托管",
            "category_id": category["id"],
        },
    )
    assert resp.status_code == 201
    link = resp.json()
    assert link["title"] == "GitHub"
    assert link["is_pinned"] is False

    resp = client.get("/api/nav/links")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.put(
        f"/api/nav/links/{link['id']}",
        json={"title": "GitHub 主页", "is_pinned": True},
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "GitHub 主页"
    assert resp.json()["is_pinned"] is True

    resp = client.delete(f"/api/nav/links/{link['id']}")
    assert resp.status_code == 204
    assert client.get("/api/nav/links").json() == []


def test_pinned_links_sorted_first(client):
    category = _create_category(client)
    base = {"category_id": category["id"]}
    client.post("/api/nav/links", json={"title": "普通", "url": "https://a.com", **base}).json()
    client.post("/api/nav/links", json={"title": "常用", "url": "https://b.com", "is_pinned": True, **base}).json()

    resp = client.get("/api/nav/links")
    assert resp.status_code == 200
    titles = [link["title"] for link in resp.json()]
    assert titles == ["常用", "普通"]

    # 分类接口返回的 links 同样按置顶优先排序
    categories = client.get("/api/nav/categories").json()
    assert [link["title"] for link in categories[0]["links"]] == ["常用", "普通"]


def test_nav_404_and_validation(client):
    assert client.put("/api/nav/categories/999", json={"name": "x"}).status_code == 404
    assert client.delete("/api/nav/links/999").status_code == 404
    assert client.post("/api/nav/links", json={"title": "", "url": "", "category_id": 1}).status_code == 422
