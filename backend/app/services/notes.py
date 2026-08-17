from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.notes import Note
from app.schemas.notes import FolderOut, ImportResult, NoteCreate, NoteOut, NoteUpdate
from app.services import tags
from app.services.note_files import delete_file, file_path_for, read_content, unique_path, write_content


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
        content=read_content(Path(note.file_path)),
        updated_at=note.updated_at,
    )


def list_notes(db: Session, folder: str | None, q: str | None) -> list[NoteOut]:
    stmt = select(Note).order_by(Note.updated_at.desc())
    if folder:
        stmt = stmt.where(Note.folder == folder)
    notes = db.scalars(stmt).all()

    results = []
    keyword = (q or "").strip().lower()
    for note in notes:
        content = read_content(Path(note.file_path))
        if keyword:
            tags_text = " ".join(tags.to_list(note.tags))
            hay = f"{note.title} {tags_text} {content}".lower()
            if keyword not in hay:
                continue
        results.append(note_to_out(note))
    return results


def list_folders(db: Session) -> list[FolderOut]:
    rows = db.execute(select(Note.folder, Note.id)).all()
    counts: dict[str, int] = {}
    for folder, _ in rows:
        counts[folder] = counts.get(folder, 0) + 1
    return [FolderOut(folder=folder, count=count) for folder, count in sorted(counts.items())]


def get_note(db: Session, note_id: int) -> NoteOut:
    return note_to_out(note_or_404(db, note_id))


def create_note(db: Session, payload: NoteCreate) -> NoteOut:
    folder = payload.folder.strip() or "未分类"
    title = payload.title.strip()
    if db.scalar(select(Note).where(Note.folder == folder, Note.title == title)):
        raise HTTPException(status_code=409, detail="同文件夹已有同名笔记，请改名或换文件夹")
    path = write_content(file_path_for(folder, title), payload.content)
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
        title = Path(upload.filename or "未命名").stem.strip() or "未命名"
        path = unique_path(target, title)
        final_title = path.stem
        if final_title != title:
            renamed.append(final_title)
        write_content(path, content)
        note = Note(folder=target, title=final_title, file_path=str(path))
        db.add(note)
        db.commit()
        db.refresh(note)
        created.append(note_to_out(note))

    return ImportResult(created=created, renamed=renamed, errors=errors)


def update_note(db: Session, note_id: int, payload: NoteUpdate) -> NoteOut:
    note = note_or_404(db, note_id)
    data = payload.model_dump(exclude_unset=True)

    if "tags" in data and data["tags"] is None:
        data["tags"] = ""
    for key in ("title", "folder", "content"):
        if data.get(key) is None:
            data.pop(key, None)

    if "tags" in data and data["tags"] is not None:
        data["tags"] = tags.to_str(data["tags"])

    new_folder = data.get("folder", note.folder).strip() or "未分类"
    new_title = data.get("title", note.title).strip()
    new_path = file_path_for(new_folder, new_title)

    if "title" in data or "folder" in data:
        if (new_folder, new_title) != (note.folder, note.title):
            existing = db.scalar(
                select(Note).where(Note.folder == new_folder, Note.title == new_title, Note.id != note.id)
            )
            if existing is not None:
                raise HTTPException(status_code=409, detail="同文件夹已有同名笔记，请改名或换文件夹")
            old_path = Path(note.file_path)
            new_path.parent.mkdir(parents=True, exist_ok=True)
            if old_path.exists() and old_path != new_path:
                old_path.rename(new_path)
            note.file_path = str(new_path)

    if "content" in data and data["content"] is not None:
        write_content(Path(note.file_path), data["content"])

    if "title" in data:
        note.title = new_title
    if "folder" in data:
        note.folder = new_folder
    if "tags" in data:
        note.tags = data["tags"]
    db.commit()
    db.refresh(note)
    return note_to_out(note)


def delete_note(db: Session, note_id: int) -> None:
    note = note_or_404(db, note_id)
    delete_file(Path(note.file_path))
    db.delete(note)
    db.commit()
