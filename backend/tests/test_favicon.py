import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services import favicon as favicon_service


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_favicon_fetch_and_cache(client, monkeypatch):
    fake_bytes = b"\x89PNG\r\n\x1a\n" + b"0" * 32

    def fake_fetch(domain):
        favicon_service.CACHE_DIR.mkdir(parents=True, exist_ok=True)
        path = favicon_service.CACHE_DIR / f"{domain}.png"
        path.write_bytes(fake_bytes)
        return path

    monkeypatch.setattr(favicon_service, "fetch_and_cache", fake_fetch)

    resp = client.get("/api/nav/favicons?domain=example.com")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/png")
    assert resp.content == fake_bytes


def test_favicon_invalid_domain(client):
    resp = client.get("/api/nav/favicons?domain=bad%20domain")
    assert resp.status_code == 400


def test_extract_icon_href():
    html = '<html><head><link rel="shortcut icon" href="/assets/fav.svg"><link rel="stylesheet" href="/app.css"></head></html>'
    assert favicon_service._extract_icon_href(html) == "/assets/fav.svg"
    assert favicon_service._extract_icon_href("<html></html>") is None


def test_negative_cache_skips_retry(monkeypatch):
    calls = {"n": 0}

    def failing_download(domain):
        calls["n"] += 1
        return None

    monkeypatch.setattr(favicon_service, "_download", failing_download)
    assert favicon_service.fetch_and_cache("never-exists.example") is None
    assert favicon_service.fetch_and_cache("never-exists.example") is None
    assert calls["n"] == 1  # 负缓存期内第二次不再发起网络请求
