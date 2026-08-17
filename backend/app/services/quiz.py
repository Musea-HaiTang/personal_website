import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

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
from app.services.quiz_yaml import apply_import, parse_quiz_yaml, preview_import


def question_or_404(db: Session, question_id: int) -> Question:
    question = db.get(Question, question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="题目不存在")
    return question


def question_to_out(question: Question) -> QuestionOut:
    return QuestionOut(
        id=question.id,
        category=question.category,
        no=question.no,
        type=question.type,
        title=question.title,
        options=options_from_str(question.options),
        accept=options_from_str(question.accept),
        answer=question.answer,
        code=question.code,
        reference_answer=question.reference_answer,
        explanation=question.explanation,
        score=question.score,
        updated_at=question.updated_at,
    )


def apply_payload(question: Question, data: dict) -> None:
    """把更新 payload 落到题目：options/accept 序列化为 JSON，跳过 None 字段。"""
    if "options" in data and data["options"] is not None:
        data["options"] = json.dumps(data["options"], ensure_ascii=False)
    if "accept" in data and data["accept"] is not None:
        data["accept"] = json.dumps(data["accept"], ensure_ascii=False)
    for key, value in data.items():
        if value is not None:
            setattr(question, key, value)


def list_questions(db: Session, category: str | None) -> list[QuestionOut]:
    stmt = select(Question).order_by(Question.category, Question.no, Question.id)
    if category:
        stmt = stmt.where(Question.category == category)
    return [question_to_out(q) for q in db.scalars(stmt).all()]


def get_question(db: Session, question_id: int) -> QuestionOut:
    return question_to_out(question_or_404(db, question_id))


def create_question(db: Session, payload: QuestionCreate) -> QuestionOut:
    question = Question(
        category=payload.category,
        no=payload.no,
        type=payload.type,
        title=payload.title,
        options=json.dumps(payload.options, ensure_ascii=False),
        accept=json.dumps(payload.accept, ensure_ascii=False),
        answer=payload.answer,
        code=payload.code,
        reference_answer=payload.reference_answer,
        explanation=payload.explanation,
        score=payload.score,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question_to_out(question)


def update_question(db: Session, question_id: int, payload: QuestionUpdate) -> QuestionOut:
    question = question_or_404(db, question_id)
    apply_payload(question, payload.model_dump(exclude_unset=True))
    db.commit()
    db.refresh(question)
    return question_to_out(question)


def delete_question(db: Session, question_id: int) -> None:
    question = question_or_404(db, question_id)
    db.delete(question)
    db.commit()


def preview_upload(db: Session, file) -> ImportPreview:
    """读取上传的题库文件：解码 → 解析校验 → 对照数据库给出新增/更新预览。"""
    raw = file.file.read()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return ImportPreview(category="", new=[], updated=[], errors=["文件编码不是 UTF-8，请转码后重试"], items=[])

    category, items, errors = parse_quiz_yaml(text)
    new, updated = preview_import(items, db)
    normalized = [ImportItem(**item) for item in items]
    return ImportPreview(category=category, new=new, updated=updated, errors=errors, items=normalized)


def confirm_import(db: Session, payload: ImportConfirm) -> ImportResult:
    items = [item.model_dump() for item in payload.items]
    imported, updated = apply_import(items, db)
    return ImportResult(imported=imported, updated=updated)
