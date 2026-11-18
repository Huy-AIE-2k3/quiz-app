"""Student Exam Service (Step 5.1).

Handles student exam catalog retrieval, detail presentation, and real-time state calculation.
Enforces strict class isolation and 0% sensitive data leakage.
"""

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.orm import Session, joinedload, selectinload

from app.core.errors import AppError
from app.core.time import Clock, compute_deadline, remaining_seconds
from app.models import Attempt, ClassMember, Exam, ExamClass, Question, User
from app.schemas.student_exam_schema import (
    StudentAnswerItem,
    StudentAttemptDetailResponse,
    StudentExamDetail,
    StudentExamListItem,
    StudentExamState,
    StudentStartAttemptResponse,
)
from app.schemas.student_question import student_view
from app.services.asset_service import batch_render_questions_assets, render_assets


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


def resume_or_finalize(
    db: Session,
    attempt: Attempt,
    now: datetime,
    grace_seconds: int = 10,
) -> StudentStartAttemptResponse:
    """Resumes an existing attempt or lazily finalizes it if past deadline + grace (Step 5.2)."""
    if attempt.status == "submitted":
        return StudentStartAttemptResponse(
            id=attempt.id,
            exam_id=attempt.exam_id,
            status="submitted",
            started_at=attempt.started_at,
            deadline_at=attempt.deadline_at,
            submitted_at=attempt.submitted_at,
            remaining_seconds=0,
            server_now=now,
        )

    # If in_progress but past deadline + grace -> lazily finalize (TC-5.2-07)
    if now >= attempt.deadline_at + timedelta(seconds=grace_seconds):
        attempt.status = "submitted"
        attempt.submitted_at = attempt.deadline_at
        db.commit()
        db.refresh(attempt)
        return StudentStartAttemptResponse(
            id=attempt.id,
            exam_id=attempt.exam_id,
            status="submitted",
            started_at=attempt.started_at,
            deadline_at=attempt.deadline_at,
            submitted_at=attempt.submitted_at,
            remaining_seconds=0,
            server_now=now,
        )

    rem = remaining_seconds(now, attempt.deadline_at)
    return StudentStartAttemptResponse(
        id=attempt.id,
        exam_id=attempt.exam_id,
        status="in_progress",
        started_at=attempt.started_at,
        deadline_at=attempt.deadline_at,
        submitted_at=None,
        remaining_seconds=rem,
        server_now=now,
    )


def start_student_attempt(
    db: Session,
    user: User,
    exam_id: uuid.UUID,
    clock: Clock,
) -> StudentStartAttemptResponse:
    """Idempotently starts or resumes a student examination session (Step 5.2).

    Enforces:
    - Atomicity & Idempotency: (exam_id, student_id) UNIQUE constraint with ON CONFLICT DO NOTHING.
    - Safe concurrency: Exactly one attempt created regardless of concurrent race conditions.
    - Content lock: Exam locked_at is set once by the first starting student.
    - Time-window validation: 409 exam_not_open / exam_closed.
    - Class isolation: 404 exam_not_found if not enrolled and no attempt.
    """
    now = clock.now()

    # 1. User active check
    if not user.is_active:
        raise AppError(code="inactive_account", message="Tài khoản bị khóa.", status_code=403)

    # 2. Get exam and check visibility
    exam = db.get(Exam, exam_id)
    if not exam or exam.status in ("draft", "archived"):
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    # 3. Check existing attempt (TC-5.2-06, TC-5.2-07)
    existing = db.scalar(
        select(Attempt).where(
            Attempt.exam_id == exam_id,
            Attempt.student_id == user.id,
        )
    )
    if existing:
        return resume_or_finalize(db, existing, now)

    # 4. Check enrollment in an assigned class (TC-5.2-05)
    enrolled_stmt = (
        select(ClassMember.student_id)
        .join(ExamClass, ExamClass.class_id == ClassMember.class_id)
        .where(
            ExamClass.exam_id == exam_id,
            ClassMember.student_id == user.id,
        )
        .limit(1)
    )
    is_enrolled = db.scalar(enrolled_stmt) is not None
    if not is_enrolled:
        raise AppError(code="exam_not_found", message="Không tìm thấy bài thi.", status_code=404)

    # 5. Check exam status and time window (TC-5.2-04)
    if exam.status != "published":
        raise AppError(code="exam_not_open", message="Đề thi hiện không mở.", status_code=409)

    if exam.open_at and now < exam.open_at:
        raise AppError(code="exam_not_open", message="Đề thi chưa tới giờ mở.", status_code=409)

    if exam.close_at and now >= exam.close_at:
        raise AppError(code="exam_closed", message="Đề thi đã đóng.", status_code=409)

    # 6. Compute authoritative deadline (TC-5.2-01, TC-5.2-04)
    deadline = compute_deadline(now, exam.duration_minutes, 0, exam.close_at)

    # 7. Idempotent insert with ON CONFLICT DO NOTHING (TC-5.2-02, TC-5.2-03)
    is_sqlite = db.bind and db.bind.dialect.name == "sqlite"
    seed = secrets.randbits(62)

    if is_sqlite:
        from sqlalchemy.dialects.sqlite import insert as sqlite_insert

        insert_stmt = (
            sqlite_insert(Attempt)
            .values(
                exam_id=exam_id,
                student_id=user.id,
                status="in_progress",
                started_at=now,
                deadline_at=deadline,
                shuffle_seed=seed,
            )
            .on_conflict_do_nothing(index_elements=["exam_id", "student_id"])
            .returning(Attempt.id)
        )
    else:
        from sqlalchemy.dialects.postgresql import insert as pg_insert

        insert_stmt = (
            pg_insert(Attempt)
            .values(
                exam_id=exam_id,
                student_id=user.id,
                status="in_progress",
                started_at=now,
                deadline_at=deadline,
                shuffle_seed=seed,
            )
            .on_conflict_do_nothing(index_elements=["exam_id", "student_id"])
            .returning(Attempt.id)
        )

    row = db.execute(insert_stmt).first()
    if row is None:
        # Lost race condition to concurrent insert -> read newly created attempt
        existing_concurrent = db.scalar(
            select(Attempt).where(
                Attempt.exam_id == exam_id,
                Attempt.student_id == user.id,
            )
        )
        if existing_concurrent:
            return resume_or_finalize(db, existing_concurrent, now)
        raise AppError(
            code="attempt_creation_failed",
            message="Không thể khởi tạo lượt làm bài.",
            status_code=500,
        )

    attempt_id = row[0]

    # 8. Lock exam content atomically on the very first attempt (TC-5.2-01, TC-5.2-08)
    db.execute(
        update(Exam).where(Exam.id == exam_id, Exam.locked_at.is_(None)).values(locked_at=now)
    )
    db.commit()

    attempt = db.get(Attempt, attempt_id)
    rem = remaining_seconds(now, attempt.deadline_at)
    return StudentStartAttemptResponse(
        id=attempt.id,
        exam_id=attempt.exam_id,
        status="in_progress",
        started_at=attempt.started_at,
        deadline_at=attempt.deadline_at,
        submitted_at=None,
        remaining_seconds=rem,
        server_now=now,
    )


def get_student_attempt_detail(
    db: Session,
    user: User,
    attempt_id: uuid.UUID,
    clock: Clock,
) -> StudentAttemptDetailResponse:
    """Retrieves full student examination attempt details for active taking or resume (Step 5.3).

    Enforces:
    - Ownership verification: 404 attempt_not_found if not found or belongs to another student.
    - Account active check: 403 inactive_account.
    - Lazy finalization: auto-finalizes if past deadline + 10s grace.
    - Deterministic shuffling: sha256(seed + id) for questions and options.
    - Zero data leakage: strict allow-list, never leaks answer keys, scores, or explanations.
    - Query optimization: batch queries <= 4 SQL statements total.
    """
    now = clock.now()

    if not user.is_active:
        raise AppError(code="inactive_account", message="Tài khoản bị khóa.", status_code=403)

    # 1. Fetch Attempt with Exam and Answers in single query + selectinloads (TC-5.3-04, TC-5.3-08)
    attempt = db.scalar(
        select(Attempt)
        .options(
            joinedload(Attempt.exam).selectinload(Exam.questions),
            selectinload(Attempt.answers),
        )
        .where(Attempt.id == attempt_id)
    )

    if not attempt or attempt.student_id != user.id:
        raise AppError(code="attempt_not_found", message="Không tìm thấy bài làm.", status_code=404)

    exam = attempt.exam
    if not exam:
        raise AppError(code="exam_not_found", message="Không tìm thấy đề thi.", status_code=404)

    # 2. Check lazy finalization (TC-5.3-06)
    deadline_at = (
        attempt.deadline_at
        if attempt.deadline_at.tzinfo is not None
        else attempt.deadline_at.replace(tzinfo=now.tzinfo)
    )
    started_at = (
        attempt.started_at
        if attempt.started_at.tzinfo is not None
        else attempt.started_at.replace(tzinfo=now.tzinfo)
    )

    if attempt.status == "in_progress" and now >= deadline_at + timedelta(seconds=10):
        attempt.status = "submitted"
        attempt.submitted_at = deadline_at
        db.commit()
        db.refresh(attempt)

    submitted_at = (
        attempt.submitted_at
        if attempt.submitted_at is None or attempt.submitted_at.tzinfo is not None
        else attempt.submitted_at.replace(tzinfo=now.tzinfo)
    )

    # 3. Deterministically order questions (TC-5.3-01, TC-5.3-02)
    questions = list(exam.questions)
    seed = attempt.shuffle_seed

    if exam.shuffle_questions:
        questions.sort(key=lambda q: hashlib.sha256(f"{seed}:{str(q.id)}".encode()).hexdigest())
    else:
        questions.sort(key=lambda q: q.position)

    # 4. Serialize questions via student_view with option shuffling (TC-5.3-03, TC-5.3-09)
    raw_question_views = [
        student_view(
            q=q,
            seed=seed,
            shuffle_options=exam.shuffle_options,
            exam_id=exam.id,
            db=None,  # Defer asset rendering to batch step to eliminate N+1 queries
        )
        for q in questions
    ]

    # 5. Batch render all image assets in a single SQL query (TC-5.3-08)
    rendered_questions = batch_render_questions_assets(
        questions_data=raw_question_views,
        exam_id=exam.id,
        db=db,
    )

    # 6. Map answers with client_seq (TC-5.3-05)
    answers_dict = {
        str(a.question_id): StudentAnswerItem(
            question_id=a.question_id,
            value=a.value or {},
            client_seq=a.client_seq or 0,
        )
        for a in attempt.answers
    }

    # 7. Compute remaining seconds (TC-5.3-07)
    rem = 0 if attempt.status == "submitted" else remaining_seconds(now, deadline_at)

    return StudentAttemptDetailResponse(
        id=attempt.id,
        exam_id=attempt.exam_id,
        exam_title=exam.title,
        status=attempt.status,
        started_at=started_at,
        deadline_at=deadline_at,
        submitted_at=submitted_at,
        remaining_seconds=rem,
        server_now=now,
        questions=rendered_questions,
        answers=answers_dict,
    )
