import re
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.note_folders import NoteFolder
from app.models.notes import Note
from app.schemas.notes import FolderCreate, FolderOut, ImportResult, NoteCreate, NoteOut
from app.services import search, tags
from app.services.markdown_store import notes_store


_ATX_H1 = re.compile(r"^#[ \t]+(.+?)[ \t]*$")


def extract_note_title(content: str) -> tuple[str, str]:
    """取正文首行 H1 作为笔记标题，并从正文中移除该行及其后的空行。

    用户笔记习惯以 `# 标题` 开头（H1 即文档标题，文件名也通常等于它）。导入时把它
    提升为 title，正文不再重复显示标题，避免阅读页出现两个大标题。首行不是 H1 时
    返回空标题，由调用方回退到文件名，正文保持不变。
    """
    text = content.replace("\r\n", "\n").replace("\r", "\n")
    lines = text.split("\n")
    m = _ATX_H1.match(lines[0])
    if not m:
        return "", content
    title = m.group(1).strip()
    i = 1
    while i < len(lines) and not lines[i].strip():
        i += 1
    return title, "\n".join(lines[i:])


def note_or_404(db: Session, note_id: int) -> Note:
    note = db.get(Note, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="笔记不存在")
    return note


def note_to_out(note: Note) -> NoteOut:
    return NoteOut(
        id=note.id,
        folder=note.folder,
        title=note.title,
        tags=tags.to_list(note.tags),
        content=notes_store.read(Path(note.file_path)),
        updated_at=note.updated_at,
    )


def list_notes(db: Session, folder: str | None, q: str | None) -> list[NoteOut]:
    stmt = select(Note).order_by(Note.updated_at.desc())
    if folder:
        stmt = stmt.where(Note.folder == folder)
    notes = db.scalars(stmt).all()

    results = []
    for note in notes:
        content = notes_store.read(Path(note.file_path))
        tags_text = " ".join(tags.to_list(note.tags))
        if not search.matches([note.title, tags_text, content], q):
            continue
        results.append(note_to_out(note))
    return results


def list_folders(db: Session) -> list[FolderOut]:
    rows = db.execute(select(Note.folder, Note.id)).all()
    counts: dict[str, int] = {}
    for folder, _ in rows:
        counts[folder] = counts.get(folder, 0) + 1
    for folder_name, in db.execute(select(NoteFolder.name)):
        counts.setdefault(folder_name, 0)
    return [FolderOut(folder=folder, count=count) for folder, count in sorted(counts.items())]


def create_folder(db: Session, payload: FolderCreate) -> FolderOut:
    name = payload.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="分类名称不能为空")
    exists = db.scalar(select(NoteFolder).where(NoteFolder.name == name)) is not None
    exists = exists or db.scalar(select(Note.id).where(Note.folder == name)) is not None
    if exists:
        raise HTTPException(status_code=409, detail="分类已存在")
    folder = NoteFolder(name=name)
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return FolderOut(folder=folder.name, count=0)


def get_note(db: Session, note_id: int) -> NoteOut:
    return note_to_out(note_or_404(db, note_id))


def create_note(db: Session, payload: NoteCreate) -> NoteOut:
    folder = payload.folder.strip() or "未分类"
    title = payload.title.strip()
    if db.scalar(select(Note).where(Note.folder == folder, Note.title == title)):
        raise HTTPException(status_code=409, detail="同文件夹已有同名笔记，请改名或换文件夹")
    path = notes_store.write(notes_store.path_for(folder, title), payload.content)
    note = Note(folder=folder, title=title, tags=tags.to_str(payload.tags), file_path=str(path))
    db.add(note)
    db.commit()
    db.refresh(note)
    return note_to_out(note)


def import_notes(db: Session, folder: str, uploads: list) -> ImportResult:
    """批量导入：UTF-8 解码 → 同名自动改名 → 落盘入库；逐文件失败不中断。"""
    target = folder.strip() or "未分类"
    created: list[NoteOut] = []
    renamed: list[str] = []
    errors: list[str] = []

    for upload in uploads:
        raw = upload.file.read()
        try:
            content = raw.decode("utf-8")
        except UnicodeDecodeError:
            errors.append(f"{upload.filename}: 编码不是 UTF-8，请转码后重新导入")
            continue
        filename_title = Path(upload.filename or "未命名").stem.strip() or "未命名"
        h1_title, body = extract_note_title(content)
        title = h1_title or filename_title
        # 文件名沿用原文件名，仅在重名时自动改名；标题来自正文 H1，与文件名解耦。
        path = notes_store.unique_path(target, filename_title)
        final_filename = path.stem
        if final_filename != filename_title:
            renamed.append(final_filename)
        notes_store.write(path, body)
        note = Note(folder=target, title=title, file_path=str(path))
        db.add(note)
        db.commit()
        db.refresh(note)
        created.append(note_to_out(note))

    return ImportResult(created=created, renamed=renamed, errors=errors)


def delete_note(db: Session, note_id: int) -> None:
    note = note_or_404(db, note_id)
    notes_store.delete(Path(note.file_path))
    db.delete(note)
    db.commit()
