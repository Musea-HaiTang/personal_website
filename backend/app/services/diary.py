from datetime import date
from pathlib import Path

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.diary import DiaryEntry
from app.schemas.diary import DiaryCreate, DiaryOut, DiaryUpdate
from app.services import search, tags
from app.services.markdown_store import diary_store


def _diary_path(day: date) -> Path:
    return diary_store.path_for(str(day))


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
        content=diary_store.read(_diary_path(entry.date)),
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
    return [
        entry_to_out(entry)
        for entry in entries
        if search.matches([entry.title, diary_store.read(_diary_path(entry.date))], q)
    ]


def get_entry(db: Session, entry_id: int) -> DiaryOut:
    return entry_to_out(entry_or_404(db, entry_id))


def create_entry(db: Session, payload: DiaryCreate) -> DiaryOut:
    existing = db.scalar(select(DiaryEntry).where(DiaryEntry.date == payload.date))
    if existing is not None:
        raise HTTPException(status_code=409, detail="该日期已有日记，请直接编辑")
    path = diary_store.write(_diary_path(payload.date), payload.content)
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
        diary_store.write(_diary_path(entry.date), data["content"])
    for key, value in data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return entry_to_out(entry)


def delete_entry(db: Session, entry_id: int) -> None:
    entry = entry_or_404(db, entry_id)
    diary_store.delete(_diary_path(entry.date))
    db.delete(entry)
    db.commit()
