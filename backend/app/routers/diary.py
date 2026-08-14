from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.diary import DiaryEntry
from app.schemas.diary import DiaryCreate, DiaryOut, DiaryUpdate
from app.services.diary_files import delete_file, read_content, write_content

router = APIRouter(prefix="/api/diary", tags=["diary"])


def _tags_to_str(tags: list[str]) -> str:
    return ",".join(tag.strip() for tag in tags if tag.strip())


def _tags_to_list(tags_str: str) -> list[str]:
    return [tag for tag in (tags_str or "").split(",") if tag.strip()]


def _get_entry_or_404(db: Session, entry_id: int) -> DiaryEntry:
    entry = db.get(DiaryEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="日记不存在")
    return entry


def _entry_to_out(entry: DiaryEntry) -> DiaryOut:
    return DiaryOut(
        id=entry.id,
        date=entry.date,
        title=entry.title,
        tags=_tags_to_list(entry.tags),
        content=read_content(entry.date),
        updated_at=entry.updated_at,
    )


@router.get("", response_model=list[DiaryOut])
def list_diary(
    day: date | None = Query(default=None),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
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
        results.append(_entry_to_out(entry))
    return results


@router.get("/{entry_id}", response_model=DiaryOut)
def get_diary(entry_id: int, db: Session = Depends(get_db)):
    entry = _get_entry_or_404(db, entry_id)
    return _entry_to_out(entry)


@router.post("", response_model=DiaryOut, status_code=201)
def create_diary(payload: DiaryCreate, db: Session = Depends(get_db)):
    existing = db.scalar(select(DiaryEntry).where(DiaryEntry.date == payload.date))
    if existing is not None:
        raise HTTPException(status_code=409, detail="该日期已有日记，请直接编辑")
    path = write_content(payload.date, payload.content)
    entry = DiaryEntry(
        date=payload.date,
        title=payload.title,
        tags=_tags_to_str(payload.tags),
        file_path=str(path),
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return _entry_to_out(entry)


@router.put("/{entry_id}", response_model=DiaryOut)
def update_diary(entry_id: int, payload: DiaryUpdate, db: Session = Depends(get_db)):
    entry = _get_entry_or_404(db, entry_id)
    data = payload.model_dump(exclude_unset=True)
    if "tags" in data and data["tags"] is not None:
        data["tags"] = _tags_to_str(data["tags"])
    if "content" in data and data["content"] is not None:
        write_content(entry.date, data["content"])
    for key, value in data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return _entry_to_out(entry)


@router.delete("/{entry_id}", status_code=204)
def delete_diary(entry_id: int, db: Session = Depends(get_db)):
    entry = _get_entry_or_404(db, entry_id)
    delete_file(entry.date)
    db.delete(entry)
    db.commit()
