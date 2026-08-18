import os
import tempfile
from pathlib import Path

# 必须在导入 app 之前设置，让配置指向独立的测试数据目录
_tmp_root = Path(tempfile.mkdtemp(prefix="personal_website_test_"))
os.environ["DATA_DIR"] = str(_tmp_root / "data")
os.environ["TIMEZONE"] = "Asia/Shanghai"
os.environ["AUTH_ENABLED"] = "false"
os.environ["EMBEDDING_MOCK"] = "true"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.database import SessionLocal
from app.main import app
from app.models.note_chunks import NoteChunk, NoteIndexJob
from app.models.notes import Note
from app.services.markdown_store import notes_store


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client
    with SessionLocal() as db:
        notes = db.scalars(select(Note)).all()
        for note in notes:
            path = Path(note.file_path)
            if path.exists():
                path.unlink()
        db.execute(delete(NoteChunk))
        db.execute(delete(NoteIndexJob))
        db.execute(delete(Note))
        db.commit()
