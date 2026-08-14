from fastapi.testclient import TestClient

from app.config import Settings, settings, now_local
from app.main import app


def test_health_returns_ok():
    with TestClient(app) as client:
        resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["timezone"] == "Asia/Shanghai"
    assert data["auth_enabled"] is False


def test_sqlite_init_creates_data_dir():
    import os

    data_dir = os.environ["DATA_DIR"]
    with TestClient(app) as client:
        client.get("/api/health")
    assert os.path.isdir(data_dir)
    assert os.path.isfile(os.path.join(data_dir, "app.db"))


def test_settings_env_override(monkeypatch):
    monkeypatch.setenv("AUTH_ENABLED", "true")
    assert Settings().auth_enabled is True


def test_settings_defaults():
    assert settings.timezone == "Asia/Shanghai"
    assert settings.auth_enabled is False


def test_now_local_uses_configured_timezone():
    dt = now_local()
    assert dt.utcoffset().total_seconds() == 8 * 3600
