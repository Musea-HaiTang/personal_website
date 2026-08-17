from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.notes import FolderOut, ImportResult, NoteCreate, NoteOut, NoteUpdate
from app.services import notes as notes_service

router = APIRouter(prefix="/api/notes", tags=["notes"])


@router.get("", response_model=list[NoteOut])
def list_notes(
    folder: str | None = Query(default=None),
    q: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    return notes_service.list_notes(db, folder, q)


@router.get("/folders", response_model=list[FolderOut])
def list_folders(db: Session = Depends(get_db)):
    return notes_service.list_folders(db)


@router.get("/{note_id}", response_model=NoteOut)
def get_note(note_id: int, db: Session = Depends(get_db)):
    return notes_service.get_note(db, note_id)


@router.post("", response_model=NoteOut, status_code=201)
def create_note(payload: NoteCreate, db: Session = Depends(get_db)):
    return notes_service.create_note(db, payload)


@router.post("/import", response_model=ImportResult)
def import_notes(
    folder: str = Form(default="未分类"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    return notes_service.import_notes(db, folder, files)


@router.put("/{note_id}", response_model=NoteOut)
def update_note(note_id: int, payload: NoteUpdate, db: Session = Depends(get_db)):
    return notes_service.update_note(db, note_id, payload)


@router.delete("/{note_id}", status_code=204)
def delete_note(note_id: int, db: Session = Depends(get_db)):
    notes_service.delete_note(db, note_id)
