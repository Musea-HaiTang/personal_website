from datetime import date
from pathlib import Path

from app.config import settings

DIARY_DIR = settings.data_dir / "diary"


def ensure_diary_dir() -> None:
    DIARY_DIR.mkdir(parents=True, exist_ok=True)


def file_path_for(day: date) -> Path:
    return DIARY_DIR / f"{day.isoformat()}.md"


def read_content(day: date) -> str:
    path = file_path_for(day)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_content(day: date, content: str) -> Path:
    ensure_diary_dir()
    path = file_path_for(day)
    path.write_text(content, encoding="utf-8")
    return path


def delete_file(day: date) -> None:
    path = file_path_for(day)
    if path.exists():
        path.unlink()
