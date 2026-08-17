import re
from pathlib import Path

from app.config import settings


class MarkdownStore:
    """Markdown 文件仓库：统一读写删与安全命名，目录根由实例配置。

    日记与笔记共用同一套文件操作，只通过不同实例的根目录区分；
    未来新增内容类型（闪念落盘、问答导出等）直接复用本仓库。
    """

    def __init__(self, root: Path):
        self.root = root

    def safe_name(self, name: str) -> str:
        """清理文件名中的非法字符，避免路径穿越与平台非法名。"""
        cleaned = re.sub(r'[\\/:*?"<>|]', "_", name or "").strip()
        return cleaned.rstrip(".") or "未命名"

    def path_for(self, *parts: str) -> Path:
        return self.root.joinpath(*(self.safe_name(p) for p in parts)).with_suffix(".md")

    def read(self, path: Path) -> str:
        if not path.exists():
            return ""
        return path.read_text(encoding="utf-8")

    def write(self, path: Path, content: str) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def delete(self, path: Path) -> None:
        if path.exists():
            path.unlink()

    def unique_path(self, *parts: str) -> Path:
        """同名文件自动改名（标题(1).md、标题(2).md…），不覆盖不丢失。"""
        base = self.path_for(*parts)
        if not base.exists():
            return base
        stem = base.stem
        for i in range(1, 10000):
            candidate = base.with_name(f"{stem}({i}).md")
            if not candidate.exists():
                return candidate
        raise RuntimeError("同名文件过多，无法自动改名")  # pragma: no cover


diary_store = MarkdownStore(settings.data_dir / "diary")
notes_store = MarkdownStore(settings.data_dir / "notes")
