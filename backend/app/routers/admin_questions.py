"""Admin Questions Router (/api/v1/admin/exams/{exam_id}/questions)."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Exam, Question, User
from app.schemas.admin_question import QuestionCreate, QuestionResponse

router = APIRouter(
    prefix="/exams/{exam_id}/questions",
    tags=["Admin Questions"],
    dependencies=[Depends(require_admin)],
)


@router.post("", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
def create_question(
    exam_id: uuid.UUID,
    payload: QuestionCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Creates a new question for an exam with strict type-specific schema validation."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    # Determine position if not explicitly supplied
    if payload.position is None:
        max_pos = db.scalar(
            select(func.coalesce(func.max(Question.position), 0)).where(Question.exam_id == exam_id)
        )
        pos = (max_pos or 0) + 1
    else:
        pos = payload.position

    # Check for warning flag (e.g. TF auto-converted scoring)
    warning_msg = None
    if payload.type == "tf" and payload.config.get("scoring") == "proportional":
        # Check if original was intended as thpt with != 4 statements
        if len(payload.config.get("statements", [])) != 4:
            warning_msg = (
                "Chế độ chấm 'thpt' chỉ áp dụng cho đúng 4 mệnh đề. "
                "Đã tự động chuyển sang 'proportional' (chia đều điểm)."
            )

    question = Question(
        exam_id=exam_id,
        position=pos,
        question_type=payload.type,
        content_md=payload.content_md,
        config=payload.config,
        answer_key=payload.answer_key,
        explanation_md=payload.explanation_md,
        points=payload.points,
        version=1,
    )
    db.add(question)
    db.commit()
    db.refresh(question)

    resp = QuestionResponse(
        id=question.id,
        exam_id=question.exam_id,
        position=question.position,
        type=question.question_type,
        content_md=question.content_md,
        points=question.points,
        config=question.config,
        answer_key=question.answer_key,
        explanation_md=question.explanation_md,
        version=question.version,
        warning=warning_msg,
    )
    return resp


@router.get("", response_model=list[QuestionResponse], status_code=status.HTTP_200_OK)
def list_questions(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Lists all questions in an exam ordered by position."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    questions = db.scalars(
        select(Question).where(Question.exam_id == exam_id).order_by(Question.position.asc())
    ).all()

    return [
        QuestionResponse(
            id=q.id,
            exam_id=q.exam_id,
            position=q.position,
            type=q.question_type,
            content_md=q.content_md,
            points=q.points,
            config=q.config,
            answer_key=q.answer_key,
            explanation_md=q.explanation_md,
            version=q.version,
        )
        for q in questions
    ]


@router.get("/{question_id}", response_model=QuestionResponse, status_code=status.HTTP_200_OK)
def get_question(
    exam_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Gets a single question in an exam with full administrative details."""
    question = db.scalar(
        select(Question).where(Question.exam_id == exam_id, Question.id == question_id)
    )
    if not question:
        raise AppError(
            code="question_not_found", message="Không tìm thấy câu hỏi.", status_code=404
        )

    return QuestionResponse(
        id=question.id,
        exam_id=question.exam_id,
        position=question.position,
        type=question.question_type,
        content_md=question.content_md,
        points=question.points,
        config=question.config,
        answer_key=question.answer_key,
        explanation_md=question.explanation_md,
        version=question.version,
    )


@router.delete("/{question_id}", status_code=status.HTTP_200_OK)
def delete_question(
    exam_id: uuid.UUID,
    question_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Deletes a question from an exam."""
    question = db.scalar(
        select(Question).where(Question.exam_id == exam_id, Question.id == question_id)
    )
    if not question:
        raise AppError(
            code="question_not_found", message="Không tìm thấy câu hỏi.", status_code=404
        )

    db.delete(question)
    db.commit()
    return {"status": "ok", "message": "Đã xóa câu hỏi thành công.", "id": str(question_id)}
