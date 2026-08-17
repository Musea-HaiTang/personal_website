from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.diary import DiaryCreate, DiaryOut, DiaryUpdate
from app.services import diary as diary_service

router = APIRouter(prefix="/api/diary", tags=["diary"])


@router.get("", response_model=list[DiaryOut])
def list_diary(
    day: date | None = Query(default=None),
    tag: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return diary_service.list_entries(db, day, tag, q)


@router.get("/{entry_id}", response_model=DiaryOut)
def get_diary(entry_id: int, db: Session = Depends(get_db)):
    return diary_service.get_entry(db, entry_id)


@router.post("", response_model=DiaryOut, status_code=201)
def create_diary(payload: DiaryCreate, db: Session = Depends(get_db)):
    return diary_service.create_entry(db, payload)


@router.put("/{entry_id}", response_model=DiaryOut)
def update_diary(entry_id: int, payload: DiaryUpdate, db: Session = Depends(get_db)):
    return diary_service.update_entry(db, entry_id, payload)


@router.delete("/{entry_id}", status_code=204)
def delete_diary(entry_id: int, db: Session = Depends(get_db)):
    diary_service.delete_entry(db, entry_id)
