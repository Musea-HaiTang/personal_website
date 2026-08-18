import time

from fastapi.testclient import TestClient

from app.services import indexing
from app.services.chunker import chunk_markdown


def _create(client: TestClient, content: str = "# 标题\n\n一段内容"):
    return client.post(
        "/api/notes",
        json={"title": "索引测试", "folder": "Python 笔记", "tags": ["基础"], "content": content},
    )


def _wait_progress(client: TestClient, done: int, timeout: float = 5.0):
    deadline = time.monotonic() + timeout
    data = client.get("/api/notes/index/progress").json()
    while time.monotonic() < deadline and (data["done"] < done or data["pending"] > 0):
        time.sleep(0.02)
        data = client.get("/api/notes/index/progress").json()
    return data


def test_chunk_markdown_splits_by_heading_and_paragraph():
    chunks = chunk_markdown("# 标题\n\n第一段。\n\n第二段。\n\n## 小节\n\n第三段。")

    assert [(chunk.heading, chunk.content) for chunk in chunks] == [
        ("标题", "第一段。"),
        ("标题", "第二段。"),
        ("小节", "第三段。"),
    ]


def test_chunk_markdown_long_block_overlaps_50_chars():
    chunks = chunk_markdown("字" * 700)

    assert len(chunks) == 2
    assert len(chunks[0].content) == 600
    assert chunks[0].content[-50:] == chunks[1].content[:50]


def test_create_note_builds_chunks_with_embedding(client):
    resp = _create(client, content="# 标题\n\n一段内容")
    assert resp.status_code == 201
    note = resp.json()

    progress = client.get("/api/notes/index/progress").json()
    assert progress["total"] == 1
    assert progress["done"] == 1
    assert progress["chunk_count"] == 1
    assert progress["pending"] == 0


def test_batch_import_indexes_in_background(client):
    resp = client.post(
        "/api/notes/import",
        data={"folder": "Python 笔记"},
        files=[
            ("files", ("A.md", "# A\n\n内容 A".encode("utf-8"), "text/markdown")),
            ("files", ("B.md", "# B\n\n内容 B".encode("utf-8"), "text/markdown")),
        ],
    )
    assert resp.status_code == 200
    assert len(resp.json()["created"]) == 2

    progress = _wait_progress(client, done=2)
    assert progress["total"] == 2
    assert progress["done"] == 2
    deadline = time.monotonic() + 2.0
    while progress["chunk_count"] < 2 and time.monotonic() < deadline:
        time.sleep(0.02)
        progress = client.get("/api/notes/index/progress").json()
    assert progress["chunk_count"] == 2
    assert progress["pending"] == 0


def test_update_rebuilds_chunks(client):
    note = _create(client, content="# 旧标题\n\n" + "旧" * 700).json()
    assert client.get("/api/notes/index/progress").json()["chunk_count"] == 2

    resp = client.put(f"/api/notes/{note['id']}", json={"content": "# 新标题\n\n新内容"})
    assert resp.status_code == 200

    progress = client.get("/api/notes/index/progress").json()
    assert progress["done"] == 1
    assert progress["chunk_count"] == 1


def test_delete_removes_chunks_and_job(client):
    note = _create(client).json()

    assert client.delete(f"/api/notes/{note['id']}").status_code == 204

    progress = client.get("/api/notes/index/progress").json()
    assert progress["total"] == 0
    assert progress["chunk_count"] == 0


def test_embedding_failure_retries_then_succeeds(client, monkeypatch):
    calls = {"n": 0}
    original = indexing.embed_texts

    def flaky(texts):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("embedding down")
        return original(texts)

    monkeypatch.setattr(indexing, "embed_texts", flaky)
    assert _create(client, content="一段内容").status_code == 201

    progress = client.get("/api/notes/index/progress").json()
    assert progress["done"] == 1
    assert calls["n"] == 2


def test_embedding_failure_marks_failed_and_note_still_browsable(client, monkeypatch):
    def always_fail(texts):
        raise RuntimeError("embedding down")

    monkeypatch.setattr(indexing, "embed_texts", always_fail)
    note = _create(client, content="一段内容")
    assert note.status_code == 201

    progress = client.get("/api/notes/index/progress").json()
    assert progress["failed"] == 1
    assert progress["chunk_count"] == 0
    assert progress["pending"] == 0
    assert client.get(f"/api/notes/{note.json()['id']}").status_code == 200
