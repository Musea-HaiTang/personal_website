import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.flash import FlashNote
from app.schemas.flash import FlashCreate, FlashOut

router = APIRouter(prefix="/api/flash", tags=["flash"])


def _get_note_or_404(db: Session, note_id: int) -> FlashNote:
    note = db.get(FlashNote, note_id)
    if note is None:
        raise HTTPException(status_code=404, detail="闪念不存在")
    return note


@router.get("", response_model=list[FlashOut])
def list_flash(
    day: datetime.date | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    """列出闪念；可按日期 / 关键词过滤（个人数据量小，内存过滤避免 SQLite 时区坑）。"""
    notes = db.scalars(select(FlashNote).order_by(FlashNote.created_at.desc())).all()
    keyword = (q or "").strip().lower()
    result = []
    for note in notes:
        if keyword and keyword not in note.content.lower():
            continue
        if day is not None and note.created_at.date() != day:
            continue
        result.append(note)
    return result


@router.post("", response_model=FlashOut, status_code=201)
def create_flash(payload: FlashCreate, db: Session = Depends(get_db)):
    note = FlashNote(content=payload.content)
    db.add(note)
    db.commit()
    db.refresh(note)
    return note


@router.delete("/{note_id}", status_code=204)
def delete_flash(note_id: int, db: Session = Depends(get_db)):
    note = _get_note_or_404(db, note_id)
    db.delete(note)
    db.commit()
