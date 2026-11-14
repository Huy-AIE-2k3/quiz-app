"""Admin Exams Router (/api/v1/admin/exams/*)."""

import random
import uuid
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session

from app.core.dependencies import require_admin
from app.core.errors import AppError
from app.db.session import get_db
from app.models import Attempt, Class, Exam, ExamClass, Question, User
from app.models.class_model import ClassMember
from app.schemas.exam_schema import (
    ExamAssignClassesPayload,
    ExamCreate,
    ExamDetailResponse,
    ExamListResponse,
    ExamPreviewResponse,
    ExamReorderQuestions,
    ExamStatusTransition,
    ExamUpdate,
    ExamValidationResult,
    ExamValidationSummary,
)
from app.schemas.student_question import student_view_list
from app.services.exam_service import (
    duplicate_exam_with_assets,
    transition_exam_status,
    validate_exam_details,
)

router = APIRouter(
    prefix="/exams",
    tags=["Admin Exams"],
    dependencies=[Depends(require_admin)],
)


def _build_exam_detail(exam: Exam, db: Session) -> ExamDetailResponse:
    """Helper to assemble an ExamDetailResponse with related aggregates."""
    # Questions and total points
    q_stats = db.execute(
        select(
            func.count(Question.id),
            func.coalesce(func.sum(Question.points), Decimal("0.00")),
        ).where(Question.exam_id == exam.id)
    ).one()
    question_count = q_stats[0] or 0
    total_points = Decimal(str(q_stats[1] or "0.00"))

    # Attempt count
    attempt_count = db.scalar(select(func.count(Attempt.id)).where(Attempt.exam_id == exam.id)) or 0

    # Assigned classes
    assigned = db.execute(
        select(Class.id, Class.name, Class.code, Class.is_archived)
        .join(ExamClass, ExamClass.class_id == Class.id)
        .where(ExamClass.exam_id == exam.id)
    ).all()
    assigned_classes = [
        {"id": row[0], "name": row[1], "code": row[2], "is_archived": row[3]} for row in assigned
    ]

    return ExamDetailResponse(
        id=exam.id,
        title=exam.title,
        description_md=exam.description_md,
        subject=exam.subject,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        open_at=exam.open_at,
        close_at=exam.close_at,
        locked_at=exam.locked_at,
        shuffle_questions=exam.shuffle_questions,
        shuffle_options=exam.shuffle_options,
        result_visibility=exam.result_visibility,
        version=exam.version,
        created_by=exam.created_by,
        created_at=exam.created_at,
        assigned_classes=assigned_classes,
        question_count=question_count,
        total_points=total_points,
        attempt_count=attempt_count,
    )


@router.post("", response_model=ExamDetailResponse, status_code=status.HTTP_201_CREATED)
def create_exam(
    payload: ExamCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Creates a new exam in draft status and optionally links initial classes."""
    exam = Exam(
        title=payload.title,
        subject=payload.subject,
        duration_minutes=payload.duration_minutes,
        description_md=payload.description_md,
        open_at=payload.open_at,
        close_at=payload.close_at,
        shuffle_questions=payload.shuffle_questions,
        shuffle_options=payload.shuffle_options,
        result_visibility=payload.result_visibility,
        status="draft",
        locked_at=None,
        version=1,
        created_by=admin.id,
    )
    db.add(exam)
    db.flush()

    if payload.class_ids:
        # Validate classes exist
        classes = db.scalars(select(Class).where(Class.id.in_(payload.class_ids))).all()
        found_ids = {c.id for c in classes}
        missing = set(payload.class_ids) - found_ids
        if missing:
            raise AppError(
                code="class_not_found",
                message=f"Một số lớp học không tồn tại: {[str(m) for m in missing]}",
                status_code=404,
            )
        for cid in payload.class_ids:
            db.add(ExamClass(exam_id=exam.id, class_id=cid))

    db.commit()
    db.refresh(exam)
    return _build_exam_detail(exam, db)


@router.get("", response_model=ExamListResponse, status_code=status.HTTP_200_OK)
def list_exams(
    status_filter: str | None = Query(default=None, alias="status"),
    subject_filter: str | None = Query(default=None, alias="subject"),
    search: str | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Lists exams with optional filtering, search, and pagination."""
    query = select(Exam)

    if status_filter:
        query = query.where(Exam.status == status_filter)
    if subject_filter:
        query = query.where(Exam.subject == subject_filter)
    if search:
        s = f"%{search.strip()}%"
        query = query.where(Exam.title.ilike(s))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    exams = db.scalars(query.order_by(Exam.created_at.desc()).limit(limit).offset(offset)).all()

    items = [_build_exam_detail(e, db) for e in exams]
    return ExamListResponse(items=items, total=total, limit=limit, offset=offset)


@router.get("/{exam_id}", response_model=ExamDetailResponse, status_code=status.HTTP_200_OK)
def get_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Retrieves full administrative details for a specific exam."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)
    return _build_exam_detail(exam, db)


@router.patch("/{exam_id}", response_model=ExamDetailResponse, status_code=status.HTTP_200_OK)
def update_exam(
    exam_id: uuid.UUID,
    payload: ExamUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Updates exam metadata with optimistic locking and content lock check."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    # Optimistic locking check
    if payload.version != exam.version:
        raise AppError(
            code="version_conflict",
            message="Dữ liệu bài thi đã bị sửa đổi bởi người khác. Vui lòng tải lại.",
            status_code=409,
        )

    # Content lock check (TC-4.2-03)
    if exam.locked_at is not None:
        forbidden_modifications = []
        if (
            payload.duration_minutes is not None
            and payload.duration_minutes != exam.duration_minutes
        ):
            forbidden_modifications.append("duration_minutes")
        if (
            payload.shuffle_questions is not None
            and payload.shuffle_questions != exam.shuffle_questions
        ):
            forbidden_modifications.append("shuffle_questions")
        if payload.shuffle_options is not None and payload.shuffle_options != exam.shuffle_options:
            forbidden_modifications.append("shuffle_options")
        if payload.subject is not None and payload.subject != exam.subject:
            forbidden_modifications.append("subject")

        if forbidden_modifications:
            raise AppError(
                code="exam_locked",
                message=(
                    f"Bài thi đã bị khóa nội dung vì đã có học sinh làm bài. "
                    f"Không được phép thay đổi: {', '.join(forbidden_modifications)}."
                ),
                status_code=409,
            )

    # Allowed fields update
    if payload.title is not None:
        exam.title = payload.title
    if payload.description_md is not None:
        exam.description_md = payload.description_md
    if payload.result_visibility is not None:
        exam.result_visibility = payload.result_visibility
    if payload.open_at is not None:
        exam.open_at = payload.open_at
    if payload.close_at is not None:
        exam.close_at = payload.close_at

    # Fields allowed only when NOT locked
    if exam.locked_at is None:
        if payload.subject is not None:
            exam.subject = payload.subject
        if payload.duration_minutes is not None:
            exam.duration_minutes = payload.duration_minutes
        if payload.shuffle_questions is not None:
            exam.shuffle_questions = payload.shuffle_questions
        if payload.shuffle_options is not None:
            exam.shuffle_options = payload.shuffle_options

    if payload.class_ids is not None:
        # Update assigned classes
        db.execute(delete(ExamClass).where(ExamClass.exam_id == exam.id))
        for cid in payload.class_ids:
            db.add(ExamClass(exam_id=exam.id, class_id=cid))

    exam.version += 1
    db.commit()
    db.refresh(exam)
    return _build_exam_detail(exam, db)


@router.post("/{exam_id}/status", response_model=ExamDetailResponse, status_code=status.HTTP_200_OK)
def change_exam_status(
    exam_id: uuid.UUID,
    payload: ExamStatusTransition,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Transitions exam lifecycle status across valid state machine edges."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    # TC-4.5-06: Idempotent handling for concurrent publish
    if exam.status == payload.status:
        return _build_exam_detail(exam, db)

    if payload.version != exam.version:
        raise AppError(
            code="version_conflict",
            message="Dữ liệu bài thi đã bị sửa đổi bởi người khác. Vui lòng tải lại.",
            status_code=409,
        )

    transition_exam_status(exam, payload.status, db)

    exam.version += 1
    db.commit()
    db.refresh(exam)
    return _build_exam_detail(exam, db)


@router.get(
    "/{exam_id}/validate",
    response_model=ExamValidationResult,
    status_code=status.HTTP_200_OK,
)
def validate_exam_endpoint(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Validates exam for publish readiness and returns validation error report."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    errors, warnings, summary_dict = validate_exam_details(exam, db)
    return ExamValidationResult(
        valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        summary=ExamValidationSummary(**summary_dict),
    )


@router.put("/{exam_id}/classes", response_model=ExamDetailResponse, status_code=status.HTTP_200_OK)
def assign_exam_classes(
    exam_id: uuid.UUID,
    payload: ExamAssignClassesPayload,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Updates the set of classes assigned to an exam (TC-4.5-04).

    If exam is locked (or students have started attempts):
    A class that currently has attempts by its students CANNOT be removed (409 cannot_remove_class).
    Adding new classes is permitted.
    """
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    requested_ids = set(payload.class_ids)
    if requested_ids:
        classes = db.scalars(select(Class).where(Class.id.in_(requested_ids))).all()
        found_ids = {c.id for c in classes}
        missing = requested_ids - found_ids
        if missing:
            raise AppError(
                code="class_not_found",
                message=f"Một số lớp học không tồn tại: {[str(m) for m in missing]}",
                status_code=404,
            )

    current_assignments = db.scalars(
        select(ExamClass).where(ExamClass.exam_id == exam.id)
    ).all()
    current_class_ids = {ea.class_id for ea in current_assignments}

    removed_class_ids = current_class_ids - requested_ids

    if removed_class_ids and exam.locked_at is not None:
        for cid in removed_class_ids:
            attempt_count = (
                db.scalar(
                    select(func.count(Attempt.id))
                    .join(ClassMember, ClassMember.student_id == Attempt.student_id)
                    .where(Attempt.exam_id == exam.id, ClassMember.class_id == cid)
                )
                or 0
            )
            if attempt_count > 0:
                cls_obj = db.get(Class, cid)
                cls_name = cls_obj.name if cls_obj else str(cid)
                raise AppError(
                    code="cannot_remove_class",
                    message=(
                        f"Không thể rút lớp '{cls_name}' khỏi bài thi vì đã có "
                        "học sinh thuộc lớp này bắt đầu làm bài."
                    ),
                    status_code=409,
                )

    db.execute(delete(ExamClass).where(ExamClass.exam_id == exam.id))
    for cid in requested_ids:
        db.add(ExamClass(exam_id=exam.id, class_id=cid))

    exam.version += 1
    db.commit()
    db.refresh(exam)
    return _build_exam_detail(exam, db)


@router.get(
    "/{exam_id}/preview",
    response_model=ExamPreviewResponse,
    status_code=status.HTTP_200_OK,
)
def get_exam_preview(
    exam_id: uuid.UUID,
    seed: int | None = Query(default=None),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Returns student-view representation of the exam and questions for teacher sandbox preview.

    TC-4.5-01:
    - Never creates any row in `attempts` or `answers`.
    - Never sets `locked_at` on the exam.
    """
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    questions = db.scalars(
        select(Question).where(Question.exam_id == exam_id).order_by(Question.position.asc())
    ).all()

    effective_seed = seed if seed is not None else 42

    student_questions = student_view_list(
        questions,
        seed=effective_seed,
        shuffle_options=exam.shuffle_options,
        exam_id=exam_id,
        db=db,
    )

    if exam.shuffle_questions and len(student_questions) > 1:
        rng = random.Random(effective_seed)
        rng.shuffle(student_questions)

    return ExamPreviewResponse(
        id=exam.id,
        title=exam.title,
        description_md=exam.description_md,
        subject=exam.subject,
        duration_minutes=exam.duration_minutes,
        status=exam.status,
        shuffle_questions=exam.shuffle_questions,
        shuffle_options=exam.shuffle_options,
        questions=student_questions,
    )


@router.post("/{exam_id}/questions/reorder", status_code=status.HTTP_200_OK)
def reorder_questions(
    exam_id: uuid.UUID,
    payload: ExamReorderQuestions,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Reorders questions in an exam using DEFERRABLE unique constraint."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    if exam.locked_at is not None:
        raise AppError(
            code="exam_locked",
            message="Không thể đổi thứ tự câu hỏi vì bài thi đã bị khóa nội dung.",
            status_code=409,
        )

    existing_questions = db.scalars(select(Question).where(Question.exam_id == exam.id)).all()
    existing_id_set = {q.id for q in existing_questions}
    requested_id_set = set(payload.ordered_ids)

    # Validate exact match (no missing, no duplicate)
    if len(payload.ordered_ids) != len(requested_id_set):
        raise AppError(
            code="invalid_question_order",
            message="Danh sách thứ tự chứa câu hỏi trùng lặp.",
            status_code=422,
        )

    if existing_id_set != requested_id_set:
        missing = existing_id_set - requested_id_set
        extra = requested_id_set - existing_id_set
        err_msg = "Danh sách câu hỏi không khớp: "
        if missing:
            err_msg += f"thiếu {[str(m) for m in missing]}; "
        if extra:
            err_msg += f"thừa {[str(e) for e in extra]}; "
        raise AppError(
            code="invalid_question_order",
            message=err_msg.strip(),
            status_code=422,
        )

    # In single transaction, reassign position = 1..n
    q_map = {q.id: q for q in existing_questions}
    for new_pos, qid in enumerate(payload.ordered_ids, start=1):
        q_map[qid].position = new_pos

    db.commit()
    return {"status": "ok", "message": "Đã đổi thứ tự câu hỏi thành công."}


@router.post(
    "/{exam_id}/duplicate",
    response_model=ExamDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
def duplicate_exam_endpoint(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> Any:
    """Duplicates an exam with all its questions and storage assets."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    new_exam = duplicate_exam_with_assets(exam, admin.id, db)
    return _build_exam_detail(new_exam, db)


@router.delete("/{exam_id}", status_code=status.HTTP_200_OK)
def delete_exam(
    exam_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> dict:
    """Deletes an exam if it is in draft or has zero attempts."""
    exam = db.get(Exam, exam_id)
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    attempt_count = db.scalar(select(func.count(Attempt.id)).where(Attempt.exam_id == exam.id)) or 0

    if exam.status != "draft" and attempt_count > 0:
        raise AppError(
            code="exam_has_attempts",
            message="Không thể xóa bài thi đã có học sinh làm bài.",
            status_code=409,
        )

    db.delete(exam)
    db.commit()
    return {"status": "ok", "message": "Đã xóa bài thi thành công.", "id": str(exam_id)}
