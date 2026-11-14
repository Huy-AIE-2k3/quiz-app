"""Student Router (/api/v1/student/*).

Protected by require_student dependency. Accessible exclusively to users with role='student'.
"""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.dependencies import require_student
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Exam, ExamClass, Question, User
from app.models.class_model import ClassMember
from app.schemas.student_question import student_view_list

router = APIRouter(
    prefix="/api/v1/student",
    tags=["Student"],
    dependencies=[Depends(require_student)],
)


@router.get("/dashboard", status_code=status.HTTP_200_OK)
def student_dashboard(student: User = Depends(require_student)) -> dict:
    """Returns student personal examination portal dashboard."""
    return {
        "status": "ok",
        "message": f"Chào mừng thí sinh {student.full_name}",
        "student_id": str(student.id),
        "username": student.username,
    }


@router.get("/exams", status_code=status.HTTP_200_OK)
def list_student_exams(
    db: Session = Depends(get_db),
    student: User = Depends(require_student),
) -> list[dict[str, Any]]:
    """Returns published exams assigned to classes that the student belongs to (TC-4.5-02)."""
    query = (
        select(Exam)
        .join(ExamClass, ExamClass.exam_id == Exam.id)
        .join(ClassMember, ClassMember.class_id == ExamClass.class_id)
        .where(
            ClassMember.student_id == student.id,
            Exam.status == "published",
        )
        .distinct()
        .order_by(Exam.created_at.desc())
    )
    exams = db.scalars(query).all()
    return [
        {
            "id": str(e.id),
            "title": e.title,
            "subject": e.subject,
            "duration_minutes": e.duration_minutes,
            "status": e.status,
            "open_at": e.open_at.isoformat() if e.open_at else None,
            "close_at": e.close_at.isoformat() if e.close_at else None,
        }
        for e in exams
    ]


@router.get("/exams/{exam_id}/questions", status_code=status.HTTP_200_OK)
def get_exam_questions(
    exam_id: uuid.UUID,
    shuffle_options: bool = Query(default=True),
    seed: int | None = Query(default=None),
    db: Session = Depends(get_db),
    student: User = Depends(require_student),
) -> list[dict[str, Any]]:
    """Returns safe student-facing questions for an exam.

    Guarantees 0% leakage of sensitive keys: answer_key, explanation_md,
    correct, accepted, values, tolerance.
    If a question in DB is corrupt, it returns marked as unavailable without crashing.
    """
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    effective_seed = seed if seed is not None else (hash(str(student.id)) % 1000000)

    questions = db.scalars(
        select(Question).where(Question.exam_id == exam_id).order_by(Question.position.asc())
    ).all()

    return student_view_list(
        questions,
        seed=effective_seed,
        shuffle_options=shuffle_options,
        exam_id=exam_id,
        db=db,
    )
