from fastapi import APIRouter, Depends, File, Query, Response, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.quiz import (
    ImportConfirm,
    ImportPreview,
    ImportResult,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
)
from app.services import quiz as quiz_service
from app.services.quiz_yaml import QUIZ_TEMPLATE

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.get("/questions", response_model=list[QuestionOut])
def list_questions(category: str | None = Query(default=None), db: Session = Depends(get_db)):
    return quiz_service.list_questions(db, category)


@router.get("/questions/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    return quiz_service.get_question(db, question_id)


@router.post("/questions", response_model=QuestionOut, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    return quiz_service.create_question(db, payload)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)):
    return quiz_service.update_question(db, question_id, payload)


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    quiz_service.delete_question(db, question_id)


@router.get("/template")
def download_template():
    return Response(
        content=QUIZ_TEMPLATE,
        media_type="text/yaml; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="quiz-template.yaml"'},
    )


@router.post("/import", response_model=ImportPreview)
def import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return quiz_service.preview_upload(db, file)


@router.post("/import/confirm", response_model=ImportResult)
def import_confirm(payload: ImportConfirm, db: Session = Depends(get_db)):
    return quiz_service.confirm_import(db, payload)
