from datetime import date

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.diary import DiaryEntry
from app.schemas.diary import DiaryCreate, DiaryOut, DiaryUpdate
from app.services import tags
from app.services.diary_files import delete_file, read_content, write_content


def entry_or_404(db: Session, entry_id: int) -> DiaryEntry:
    entry = db.get(DiaryEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    return entry


def entry_to_out(entry: DiaryEntry) -> DiaryOut:
    return DiaryOut(
        id=entry.id,
        date=entry.date,
        title=entry.title,
        tags=tags.to_list(entry.tags),
        content=read_content(entry.date),
        updated_at=entry.updated_at,
    )


def list_entries(
    db: Session,
    day: date | None = None,
    tag: str | None = None,
    q: str | None = None,
) -> list[DiaryOut]:
    stmt = select(DiaryEntry).order_by(DiaryEntry.date.desc())
    if day is not None:
        stmt = stmt.where(DiaryEntry.date == day)
    if tag:
        stmt = stmt.where(DiaryEntry.tags.contains(tag))
    entries = db.scalars(stmt).all()

    results = []
    keyword = (q or "").strip().lower()
    for entry in entries:
        if keyword and keyword not in entry.title.lower() and keyword not in read_content(entry.date).lower():
            continue
        results.append(entry_to_out(entry))
    return results


def get_entry(db: Session, entry_id: int) -> DiaryOut:
    return entry_to_out(entry_or_404(db, entry_id))


def create_entry(db: Session, payload: DiaryCreate) -> DiaryOut:
    existing = db.scalar(select(DiaryEntry).where(DiaryEntry.date == payload.date))
    if existing is not None:
        raise HTTPException(status_code=409, detail="该日期已有日记，请直接编辑")
    path = write_content(payload.date, payload.content)
    entry = DiaryEntry(
        date=payload.date,
        title=payload.title,
        tags=tags.to_str(payload.tags),
        file_path=str(path),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)


def update_entry(db: Session, entry_id: int, payload: DiaryUpdate) -> DiaryOut:
    entry = entry_or_404(db, entry_id)
    data = payload.model_dump(exclude_unset=True)
    if "tags" in data and data["tags"] is not None:
        data["tags"] = tags.to_str(data["tags"])
    if "content" in data and data["content"] is not None:
        write_content(entry.date, data["content"])
    for key, value in data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)


def delete_entry(db: Session, entry_id: int) -> None:
    entry = entry_or_404(db, entry_id)
    delete_file(entry.date)
    db.delete(entry)
    db.commit()
