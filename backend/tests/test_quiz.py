import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.main import app
from app.models.quiz import Question


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        db.execute(delete(Question))
        db.commit()


VALID_YAML = """
category: Python
questions:
  - type: choice
    no: "1.1"
    score: 5
    title: 下面哪个是 Python 装饰器的正确理解？
    options:
      - 装饰器是接收函数并返回新函数的可调用对象
      - 装饰器只能修饰类方法
      - 被 @ 装饰的函数会立即执行
      - 装饰器是 Python 3 才有的特性
    answer: A
    explanation: 装饰器本质是接收函数并返回新函数的可调用对象。

  - type: fill
    no: "1.2"
    score: 10
    title: 补全装饰器：返回内部函数
    code: |
      def timer(fn):
          def wrap(*a, **kw):
              return fn(*a, **kw)
          return ____
    answer: wrap
    explanation: 装饰器要把 wrap 返回出去替换原函数。
"""


def _upload(client: TestClient, content: str, filename: str = "python.yaml"):
    return client.post(
        "/api/quiz/import",
        files={"file": (filename, content.encode("utf-8"), "text/yaml")},
    )


def test_question_crud(client):
    resp = client.post(
        "/api/quiz/questions",
        json={
            "category": "Python",
            "no": "9.9",
            "type": "choice",
            "title": "测试题",
            "options": ["a", "b", "c", "d"],
            "answer": "B",
            "score": 5,
        },
    )
    assert resp.status_code == 201
    qid = resp.json()["id"]

    listed = client.get("/api/quiz/questions", params={"category": "Python"}).json()
    assert [q["title"] for q in listed] == ["测试题"]

    upd = client.put(f"/api/quiz/questions/{qid}", json={"score": 10, "answer": "C"}).json()
    assert upd["score"] == 10
    assert upd["answer"] == "C"

    assert client.delete(f"/api/quiz/questions/{qid}").status_code == 204
    assert client.get("/api/quiz/questions").json() == []


def test_import_preview_and_confirm(client):
    preview = _upload(client, VALID_YAML).json()
    assert preview["category"] == "Python"
    assert len(preview["new"]) == 2
    assert preview["errors"] == []

    result = client.post("/api/quiz/import/confirm", json={"items": preview["items"]}).json()
    assert result == {"imported": 2, "updated": 0}

    questions = client.get("/api/quiz/questions", params={"category": "Python"}).json()
    assert len(questions) == 2
    choice = next(q for q in questions if q["type"] == "choice")
    assert choice["options"] == [
        "装饰器是接收函数并返回新函数的可调用对象",
        "装饰器只能修饰类方法",
        "被 @ 装饰的函数会立即执行",
        "装饰器是 Python 3 才有的特性",
    ]
    assert choice["answer"] == "A"
    fill = next(q for q in questions if q["type"] == "fill")
    assert fill["answer"] == "wrap"
    assert "____" in fill["code"]


def test_import_same_key_updates(client):
    _upload(client, VALID_YAML)
    client.post("/api/quiz/import/confirm", json={"items": _upload(client, VALID_YAML).json()["items"]})

    changed = VALID_YAML.replace("answer: A", "answer: B")
    preview = _upload(client, changed).json()
    assert preview["new"] == []
    assert len(preview["updated"]) == 2
    result = client.post("/api/quiz/import/confirm", json={"items": preview["items"]}).json()
    assert result == {"imported": 0, "updated": 2}

    questions = client.get("/api/quiz/questions", params={"category": "Python"}).json()
    assert next(q for q in questions if q["type"] == "choice")["answer"] == "B"


def test_import_invalid_yaml_reports_errors(client):
    bad = """
category: Python
questions:
  - type: choice
    title: 选项数量不对
    options: [a, b]
    answer: A
  - type: fill
    title: 缺答案
    code: |
      x = ____
  - type: choice
    title: 答案字母非法
    options: [a, b, c, d]
    answer: E
"""
    preview = _upload(client, bad).json()
    assert len(preview["errors"]) == 3
    assert any("固定 4 项" in e for e in preview["errors"])
    assert any("缺少 answer" in e for e in preview["errors"])
    assert any("A/B/C/D" in e for e in preview["errors"])
    assert preview["items"] == []

    preview_none = _upload(client, "category: Python\nquestions: []\n").json()
    assert len(preview_none["errors"]) == 1


def test_import_non_utf8(client):
    resp = client.post("/api/quiz/import", files={"file": ("bad.yaml", b"\xff\xfe\x00", "text/yaml")})
    data = resp.json()
    assert len(data["errors"]) == 1
    assert "UTF-8" in data["errors"][0]


def test_download_template(client):
    resp = client.get("/api/quiz/template")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("text/yaml")
    assert "quiz-template.yaml" in resp.headers["content-disposition"]
    assert "category: Python" in resp.text
