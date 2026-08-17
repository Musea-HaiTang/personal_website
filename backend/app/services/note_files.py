import re
from pathlib import Path

from app.config import settings

NOTES_DIR = settings.data_dir / "notes"


def ensure_notes_dir() -> None:
    NOTES_DIR.mkdir(parents=True, exist_ok=True)


def safe_name(name: str) -> str:
    """清理文件名中的非法字符，避免路径穿越与平台非法名。"""
    cleaned = re.sub(r'[\\/:*?"<>|]', "_", name or "").strip()
    cleaned = cleaned.rstrip(".") or "未命名"
    return cleaned


def file_path_for(folder: str, title: str) -> Path:
    return NOTES_DIR / safe_name(folder or "未分类") / f"{safe_name(title)}.md"


def unique_path(folder: str, title: str) -> Path:
    """同名文件自动改名（标题(1).md、标题(2).md…），不覆盖不丢失。"""
    base = file_path_for(folder, title)
    if not base.exists():
        return base
    stem = base.stem
    for i in range(1, 10000):
        candidate = base.with_name(f"{stem}({i}).md")
        if not candidate.exists():
            return candidate
    raise RuntimeError("同名文件过多，无法自动改名")  # pragma: no cover


def read_content(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def write_content(path: Path, content: str) -> Path:
    ensure_notes_dir()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def delete_file(path: Path) -> None:
    if path.exists():
        path.unlink()
