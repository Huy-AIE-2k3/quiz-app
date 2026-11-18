"""Student Exam Service (Step 5.1).

Handles student exam catalog retrieval, detail presentation, and real-time state calculation.
Enforces strict class isolation and 0% sensitive data leakage.
"""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.models import Attempt, ClassMember, Exam, ExamClass, Question
from app.schemas.student_exam_schema import (
    StudentExamDetail,
    StudentExamListItem,
    StudentExamState,
)
from app.services.asset_service import render_assets


def compute_student_exam_state(
    exam: Exam,
    attempt: Attempt | None,
    now: datetime,
) -> StudentExamState:
    """Computes authoritative real-time student exam state using server clock.

    State priority:
    1. If student has an attempt:
       - attempt.released is True -> 'result_available'
       - attempt.status == 'submitted' -> 'submitted'
       - attempt.status == 'in_progress' -> 'in_progress'
    2. If student has no attempt:
       - exam.status == 'closed' or (close_at and now > close_at) -> 'closed'
       - exam.open_at and now < exam.open_at -> 'upcoming'
       - Otherwise -> 'open'
    """
    if attempt is not None:
        if getattr(attempt, "released", False):
            return "result_available"
        if attempt.status == "submitted":
            return "submitted"
        if attempt.status == "in_progress":
            return "in_progress"

    if exam.status == "closed":
        return "closed"
    if exam.close_at is not None and now > exam.close_at:
        return "closed"
    if exam.open_at is not None and now < exam.open_at:
        return "upcoming"
    return "open"


def get_student_exams(
    db: Session,
    student_id: uuid.UUID,
    now: datetime,
) -> list[StudentExamListItem]:
    """Retrieves all visible exams for the student with dynamic real-time states.

    Enforces:
    - Isolation: Enrolled classes only or prior attempts.
    - Zero duplicates: Even if student is in multiple classes assigned to the same exam.
    - Status filtering: draft and archived exams are strictly hidden.
    """
    enrolled_in_class = (
        select(1)
        .select_from(ExamClass)
        .join(ClassMember, ClassMember.class_id == ExamClass.class_id)
        .where(
            ExamClass.exam_id == Exam.id,
            ClassMember.student_id == student_id,
        )
        .correlate(Exam)
        .exists()
    )

    has_attempt = (
        select(1)
        .select_from(Attempt)
        .where(
            Attempt.exam_id == Exam.id,
            Attempt.student_id == student_id,
        )
        .correlate(Exam)
        .exists()
    )

    q_count_subq = (
        select(func.count(Question.id))
        .where(Question.exam_id == Exam.id)
        .correlate(Exam)
        .scalar_subquery()
    )

    stmt = (
        select(Exam, Attempt, q_count_subq)
        .outerjoin(
            Attempt,
            and_(
                Attempt.exam_id == Exam.id,
                Attempt.student_id == student_id,
            ),
        )
        .where(
            Exam.status.notin_(["draft", "archived"]),
            or_(
                and_(Exam.status == "published", enrolled_in_class),
                and_(Exam.status.in_(["published", "closed"]), has_attempt),
            ),
        )
        .order_by(Exam.created_at.desc(), Exam.id.desc())
    )

    results = db.execute(stmt).all()
    items: list[StudentExamListItem] = []
    for exam, attempt, q_count in results:
        state = compute_student_exam_state(exam, attempt, now)
        items.append(
            StudentExamListItem(
                id=exam.id,
                title=exam.title,
                subject=exam.subject,
                duration_minutes=exam.duration_minutes,
                question_count=int(q_count or 0),
                open_at=exam.open_at,
                close_at=exam.close_at,
                state=state,
                attempt_id=attempt.id if attempt else None,
            )
        )
    return items


def get_student_exam_detail(
    db: Session,
    student_id: uuid.UUID,
    exam_id: uuid.UUID,
    now: datetime,
) -> StudentExamDetail:
    """Retrieves student exam introduction view.

    Returns 404 (not 403) if exam does not exist, is draft/archived, or student
    is not enrolled in an assigned class and has no prior attempt.
    """
    exam = db.get(Exam, exam_id)
    if not exam or exam.status in ("draft", "archived"):
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    attempt = db.scalar(
        select(Attempt).where(
            Attempt.exam_id == exam_id,
            Attempt.student_id == student_id,
        )
    )

    if attempt is None:
        # Must be enrolled in an assigned class and exam must be published
        if exam.status != "published":
            raise AppError(
                code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404
            )

        enrolled_stmt = (
            select(ClassMember.student_id)
            .join(ExamClass, ExamClass.class_id == ClassMember.class_id)
            .where(
                ExamClass.exam_id == exam_id,
                ClassMember.student_id == student_id,
            )
            .limit(1)
        )
        is_enrolled = db.scalar(enrolled_stmt) is not None
        if not is_enrolled:
            raise AppError(
                code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404
            )

    # Render description markdown assets
    rendered_desc = render_assets(exam.description_md or "", exam_id, db)

    # Calculate question count and total points
    questions = db.scalars(select(Question).where(Question.exam_id == exam_id)).all()
    question_count = len(questions)
    total_points = sum((q.points for q in questions), Decimal("0.00"))

    state = compute_student_exam_state(exam, attempt, now)
    can_start = state in ("open", "in_progress")

    return StudentExamDetail(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        description_md=rendered_desc or "",
        duration_minutes=exam.duration_minutes,
        question_count=question_count,
        total_points=total_points,
        open_at=exam.open_at,
        close_at=exam.close_at,
        state=state,
        attempt_id=attempt.id if attempt else None,
        can_start=can_start,
    )
