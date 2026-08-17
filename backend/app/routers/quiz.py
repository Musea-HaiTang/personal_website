import json

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.quiz import Question
from app.schemas.quiz import (
    ImportConfirm,
    ImportItem,
    ImportPreview,
    ImportResult,
    QuestionCreate,
    QuestionOut,
    QuestionUpdate,
    options_from_str,
)
from app.services.quiz_yaml import QUIZ_TEMPLATE, apply_import, parse_quiz_yaml, preview_import

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


def _question_to_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        category=question.category,
        no=question.no,
        type=question.type,
        title=question.title,
        options=options_from_str(question.options),
        answer=question.answer,
        code=question.code,
        reference_answer=question.reference_answer,
        explanation=question.explanation,
        score=question.score,
        updated_at=question.updated_at,
    )


def _get_question_or_404(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


def _apply_payload(question: Question, data: dict) -> None:
    if "options" in data and data["options"] is not None:
        data["options"] = json.dumps(data["options"], ensure_ascii=False)
    for key, value in data.items():
        setattr(question, key, value)


@router.get("/questions", response_model=list[QuestionOut])
def list_questions(category: str | None = Query(default=None), db: Session = Depends(get_db)):
    stmt = select(Question).order_by(Question.category, Question.no, Question.id)
    if category:
        stmt = stmt.where(Question.category == category)
    return [_question_to_out(q) for q in db.scalars(stmt).all()]


@router.get("/questions/{question_id}", response_model=QuestionOut)
def get_question(question_id: int, db: Session = Depends(get_db)):
    return _question_to_out(_get_question_or_404(db, question_id))


@router.post("/questions", response_model=QuestionOut, status_code=201)
def create_question(payload: QuestionCreate, db: Session = Depends(get_db)):
    question = Question(
        category=payload.category,
        no=payload.no,
        type=payload.type,
        title=payload.title,
        options=json.dumps(payload.options, ensure_ascii=False),
        answer=payload.answer,
        code=payload.code,
        reference_answer=payload.reference_answer,
        explanation=payload.explanation,
        score=payload.score,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return _question_to_out(question)


@router.put("/questions/{question_id}", response_model=QuestionOut)
def update_question(question_id: int, payload: QuestionUpdate, db: Session = Depends(get_db)):
    question = _get_question_or_404(db, question_id)
    _apply_payload(question, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(question)
    return _question_to_out(question)


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(question_id: int, db: Session = Depends(get_db)):
    question = _get_question_or_404(db, question_id)
    db.delete(question)
    db.commit()


@router.get("/template")
def download_template():
    return Response(
        content=QUIZ_TEMPLATE,
        media_type="text/yaml; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="quiz-template.yaml"'},
    )


@router.post("/import", response_model=ImportPreview)
def import_preview(file: UploadFile = File(...), db: Session = Depends(get_db)):
    raw = file.file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ImportPreview(category="", new=[], updated=[], errors=["文件编码不是 UTF-8，请转码后重试"], items=[])

    category, items, errors = parse_quiz_yaml(text)
    new, updated = preview_import(items, db)
    normalized = [ImportItem(**item) for item in items]
    return ImportPreview(category=category, new=new, updated=updated, errors=errors, items=normalized)


@router.post("/import/confirm", response_model=ImportResult)
def import_confirm(payload: ImportConfirm, db: Session = Depends(get_db)):
    items = [item.model_dump() for item in payload.items]
    imported, updated = apply_import(items, db)
    return ImportResult(imported=imported, updated=updated)
