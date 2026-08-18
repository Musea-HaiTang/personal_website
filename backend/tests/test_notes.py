from fastapi.testclient import TestClient

from app.services.markdown_store import notes_store


def _create(client: TestClient, title: str = "装饰器原理", folder: str = "Python 笔记", tags=None, content: str = "# 装饰器"):
    return client.post("/api/notes", json={"title": title, "folder": folder, "tags": tags or ["基础"], "content": content})


def test_note_create_writes_markdown_file(client):
    resp = _create(client, content="# 装饰器\n\n本质是返回新函数。")
    assert resp.status_code == 201
    note = resp.json()
    assert note["title"] == "装饰器原理"
    assert note["folder"] == "Python 笔记"
    assert note["tags"] == ["基础"]

    path = notes_store.root / "Python 笔记" / "装饰器原理.md"
    assert path.exists()
    assert path.read_text(encoding="utf-8") == "# 装饰器\n\n本质是返回新函数。"


def test_note_duplicate_paste_conflict(client):
    _create(client)
    resp = _create(client)
    assert resp.status_code == 409


def test_note_list_filter_and_search(client):
    _create(client, title="装饰器", content="装饰器返回新函数")
    _create(client, title="响应式原理", folder="Vue3 笔记", content="Proxy 代理对象")

    by_folder = client.get("/api/notes", params={"folder": "Vue3 笔记"}).json()
    assert [n["title"] for n in by_folder] == ["响应式原理"]

    by_keyword = client.get("/api/notes", params={"q": "Proxy"}).json()
    assert [n["title"] for n in by_keyword] == ["响应式原理"]

    by_tag = client.get("/api/notes", params={"q": "基础"}).json()
    assert len(by_tag) == 2


def test_notes_folders_counts(client):
    _create(client, title="装饰器原理", folder="Python 笔记")
    _create(client, title="生成器与迭代器", folder="Python 笔记")
    _create(client, folder="Vue3 笔记")

    folders = client.get("/api/notes/folders").json()
    assert {"folder": "Python 笔记", "count": 2} in folders
    assert {"folder": "Vue3 笔记", "count": 1} in folders


def test_empty_note_folder_persists(client):
    resp = client.post("/api/notes/folders", json={"name": "待整理"})
    assert resp.status_code == 201
    assert resp.json() == {"folder": "待整理", "count": 0}

    folders = client.get("/api/notes/folders").json()
    assert {"folder": "待整理", "count": 0} in folders

    assert client.post("/api/notes/folders", json={"name": "待整理"}).status_code == 409
    assert client.post("/api/notes/folders", json={"name": "   "}).status_code == 422


def test_note_import_autorename_and_errors(client):
    resp = client.post(
        "/api/notes/import",
        data={"folder": "Python 笔记"},
        files=[
            ("files", ("装饰器.md", "# 装饰器内容".encode("utf-8"), "text/markdown")),
            ("files", ("装饰器.md", "# 另一篇".encode("utf-8"), "text/markdown")),
            ("files", ("乱码.md", b"\xff\xfe\x00\x01", "text/markdown")),
        ],
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["created"]) == 2
    assert data["renamed"] == ["装饰器(1)"]
    assert len(data["errors"]) == 1
    assert "UTF-8" in data["errors"][0]

    notes = client.get("/api/notes").json()
    titles = sorted(n["title"] for n in notes)
    assert titles == ["装饰器", "装饰器(1)"]


def test_note_edit_and_index_routes_are_removed(client):
    note = _create(client).json()

    assert client.put(f"/api/notes/{note['id']}", json={"content": "新内容"}).status_code == 405
    assert client.get("/api/notes/index/progress").status_code == 404


def test_note_delete_removes_file(client):
    note = _create(client).json()
    assert client.delete(f"/api/notes/{note['id']}").status_code == 204
    assert not (notes_store.root / "Python 笔记" / "装饰器原理.md").exists()
    assert client.get("/api/notes").json() == []


def test_note_validation(client):
    assert client.post("/api/notes", json={"title": "", "content": ""}).status_code == 422
