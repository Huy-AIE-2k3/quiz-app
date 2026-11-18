"""Unit and Concurrency Integration Tests for Step 5.4: Save Student Answer.

Test Cases:
- TC-5.4-01: Save answer successfully, client_seq and updated_at are updated
- TC-5.4-02: Stale network packet with smaller client_seq is ignored without overwriting
- TC-5.4-03: Save answer after deadline + grace is rejected with 409 attempt_closed
- TC-5.4-04: Save answer on already submitted attempt is rejected with 409 attempt_closed
- TC-5.4-05: Save answer for question not belonging to exam returns 404 question_not_found
- TC-5.4-06: Invalid answer schema for question type is rejected with 422 invalid_answer_schema
- TC-5.4-07: Answer reported as saved is guaranteed to be persisted in DB
- TC-5.4-08: Two concurrent saves for different questions run in parallel via FOR SHARE
"""

import concurrent.futures
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import AppError
from app.core.time import FakeClock
from app.db.base import Base
from app.db.session import get_engine
from app.models import Answer, Attempt, Exam, Question, User
from app.schemas.student_exam_schema import StudentSaveAnswerRequest
from app.services.student_exam_service import save_student_answer


def create_test_user(
    session,
    username: str,
    role: str = "student",
    is_active: bool = True,
    full_name: str = "Test User",
) -> User:
    u = User(
        id=uuid.uuid4(),
        username=username,
        full_name=full_name,
        role=role,
        is_active=is_active,
        hashed_password="mock_hashed_password_123",
    )
    session.add(u)
    session.flush()
    return u


def create_test_exam(session, admin_id: uuid.UUID, title: str = "Đề Kiểm Tra") -> Exam:
    exam = Exam(
        id=uuid.uuid4(),
        title=title,
        subject="toan",
        duration_minutes=45,
        status="published",
        shuffle_questions=True,
        shuffle_options=True,
        created_by=admin_id,
    )
    session.add(exam)
    session.flush()
    return exam


def create_test_question(
    session,
    exam_id: uuid.UUID,
    position: int = 1,
    q_type: str = "mcq",
    config: dict | None = None,
    answer_key: dict | None = None,
) -> Question:
    if config is None:
        if q_type == "mcq":
            config = {
                "options": [
                    {"id": "o1", "content_md": "Lựa chọn 1"},
                    {"id": "o2", "content_md": "Lựa chọn 2"},
                ]
            }
        elif q_type == "tf":
            config = {
                "statements": [
                    {"id": "s1", "content_md": "Mệnh đề 1"},
                    {"id": "s2", "content_md": "Mệnh đề 2"},
                ],
                "scoring": "thpt",
            }
        elif q_type == "short_text":
            config = {"grading": "auto"}
        elif q_type == "short_number":
            config = {"tolerance": "0.01", "tolerance_type": "abs"}
        else:
            config = {}

    if answer_key is None:
        if q_type == "mcq":
            answer_key = {"correct": "o1"}
        elif q_type == "tf":
            answer_key = {"s1": True, "s2": False}
        elif q_type == "short_text":
            answer_key = {"accepted": ["dap an"]}
        elif q_type == "short_number":
            answer_key = {"values": ["42"]}
        else:
            answer_key = {}

    q = Question(
        id=uuid.uuid4(),
        exam_id=exam_id,
        position=position,
        question_type=q_type,
        content_md=f"Nội dung câu hỏi {position}",
        config=config,
        answer_key=answer_key,
        points=Decimal("1.00"),
    )
    session.add(q)
    session.flush()
    return q


@pytest.fixture
def test_db_session():
    """In-memory SQLite database session with complete table schema."""
    for table in Base.metadata.tables.values():
        for c in list(table.constraints):
            if getattr(c, "deferrable", False):
                c.deferrable = None
                c.initially = None

    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    session = session_factory()
    yield session, engine
    session.close()


# ==============================================================================
# TC-5.4-01: Save Answer Success, client_seq & updated_at Updated
# ==============================================================================
def test_tc_5_4_01_save_answer_success(test_db_session):
    """TC-5.4-01: Saving an answer updates client_seq and updated_at properly."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_01", role="admin")
    student = create_test_user(session, "student_54_01", role="student")
    exam = create_test_exam(session, admin.id)
    q = create_test_question(session, exam.id, 1, "mcq")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # First save: client_seq = 1
    req1 = StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1)
    res1 = save_student_answer(session, student, attempt.id, q.id, req1, clock)

    assert res1.status == "saved"
    assert res1.client_seq == 1
    assert res1.question_id == q.id
    assert res1.value == {"selected": "o1"}

    # Verify DB state
    db_ans = session.scalars(
        select(Answer).where(Answer.attempt_id == attempt.id, Answer.question_id == q.id)
    ).first()
    assert db_ans is not None
    assert db_ans.client_seq == 1
    assert db_ans.value == {"selected": "o1"}

    # Second save with higher client_seq: client_seq = 2
    clock.advance(seconds=15)
    req2 = StudentSaveAnswerRequest(value={"selected": "o2"}, client_seq=2)
    res2 = save_student_answer(session, student, attempt.id, q.id, req2, clock)

    assert res2.status == "saved"
    assert res2.client_seq == 2
    assert res2.value == {"selected": "o2"}

    session.refresh(db_ans)
    assert db_ans.client_seq == 2
    assert db_ans.value == {"selected": "o2"}


# ==============================================================================
# TC-5.4-02: Stale Network Packet Ignored
# ==============================================================================
def test_tc_5_4_02_stale_packet_ignored(test_db_session):
    """TC-5.4-02: Delayed packet with client_seq <= existing is ignored."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_02", role="admin")
    student = create_test_user(session, "student_54_02", role="student")
    exam = create_test_exam(session, admin.id)
    q = create_test_question(session, exam.id, 1, "mcq")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # Save with client_seq = 5
    req1 = StudentSaveAnswerRequest(value={"selected": "o2"}, client_seq=5)
    res1 = save_student_answer(session, student, attempt.id, q.id, req1, clock)
    assert res1.status == "saved"
    assert res1.client_seq == 5

    # Out-of-order packet arrives with client_seq = 3
    req_stale = StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=3)
    res_stale = save_student_answer(session, student, attempt.id, q.id, req_stale, clock)

    assert res_stale.status == "ignored"
    assert res_stale.client_seq == 5
    assert res_stale.value == {"selected": "o2"}

    # Duplicate packet with client_seq = 5
    res_dup = save_student_answer(session, student, attempt.id, q.id, req1, clock)
    assert res_dup.status == "ignored"
    assert res_dup.client_seq == 5

    # Verify DB was NOT overwritten
    db_ans = session.scalars(
        select(Answer).where(Answer.attempt_id == attempt.id, Answer.question_id == q.id)
    ).first()
    assert db_ans.client_seq == 5
    assert db_ans.value == {"selected": "o2"}


# ==============================================================================
# TC-5.4-03: Save After Deadline + Grace Period Rejected (409 attempt_closed)
# ==============================================================================
def test_tc_5_4_03_save_after_deadline_grace_rejected(test_db_session):
    """TC-5.4-03: Saving answer after deadline + 10s grace is rejected with 409 attempt_closed."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_03", role="admin")
    student = create_test_user(session, "student_54_03", role="student")
    exam = create_test_exam(session, admin.id)
    q = create_test_question(session, exam.id, 1, "mcq")

    deadline = now + timedelta(minutes=45)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=deadline,
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # Advance clock past deadline + 10s grace (e.g. 11 seconds past deadline)
    clock.advance(seconds=45 * 60 + 11)

    req = StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q.id, req, clock)

    assert exc.value.status_code == 409
    assert exc.value.code == "attempt_closed"

    # Verify attempt was lazily marked as submitted with submitted_at = deadline
    session.refresh(attempt)
    assert attempt.status == "submitted"
    assert attempt.submitted_at.replace(tzinfo=UTC) == deadline


# ==============================================================================
# TC-5.4-04: Save on Already Submitted Attempt Rejected (409)
# ==============================================================================
def test_tc_5_4_04_save_when_submitted_rejected(test_db_session):
    """TC-5.4-04: Saving on attempt with status='submitted' returns 409 attempt_closed."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_04", role="admin")
    student = create_test_user(session, "student_54_04", role="student")
    exam = create_test_exam(session, admin.id)
    q = create_test_question(session, exam.id, 1, "mcq")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="submitted",
        started_at=now - timedelta(minutes=30),
        deadline_at=now + timedelta(minutes=15),
        submitted_at=now - timedelta(minutes=5),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    req = StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q.id, req, clock)

    assert exc.value.status_code == 409
    assert exc.value.code == "attempt_closed"


# ==============================================================================
# TC-5.4-05: Question Not in Exam Rejected (404 question_not_found)
# ==============================================================================
def test_tc_5_4_05_question_not_in_exam_rejected(test_db_session):
    """TC-5.4-05: Saving answer for question belonging to another exam returns 404."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_05", role="admin")
    student = create_test_user(session, "student_54_05", role="student")

    exam1 = create_test_exam(session, admin.id, title="Đề Thi 1")
    exam2 = create_test_exam(session, admin.id, title="Đề Thi 2")

    q_other = create_test_question(session, exam2.id, 1, "mcq")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam1.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    req = StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_other.id, req, clock)

    assert exc.value.status_code == 404
    assert exc.value.code == "question_not_found"

    # Non-existent random question_id
    with pytest.raises(AppError) as exc_none:
        save_student_answer(session, student, attempt.id, uuid.uuid4(), req, clock)

    assert exc_none.value.status_code == 404
    assert exc_none.value.code == "question_not_found"


# ==============================================================================
# TC-5.4-06: Invalid Answer Schema Rejected (422 invalid_answer_schema)
# ==============================================================================
def test_tc_5_4_06_invalid_answer_schema_rejected(test_db_session):
    """TC-5.4-06: Invalid answer format for question type is rejected with 422."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_06", role="admin")
    student = create_test_user(session, "student_54_06", role="student")
    exam = create_test_exam(session, admin.id)

    q_mcq = create_test_question(session, exam.id, 1, "mcq")
    q_tf = create_test_question(session, exam.id, 2, "tf")
    q_num = create_test_question(session, exam.id, 3, "short_number")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # 1. MCQ with non-string selected
    req_bad_mcq1 = StudentSaveAnswerRequest(value={"selected": 1234}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_mcq.id, req_bad_mcq1, clock)
    assert exc.value.status_code == 422
    assert exc.value.code == "invalid_answer_schema"

    # 2. MCQ with non-existent option id
    req_bad_mcq2 = StudentSaveAnswerRequest(value={"selected": "o999_invalid"}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_mcq.id, req_bad_mcq2, clock)
    assert exc.value.status_code == 422
    assert exc.value.code == "invalid_answer_schema"

    # 3. TF with non-boolean statement value
    req_bad_tf1 = StudentSaveAnswerRequest(value={"statements": {"s1": "dung"}}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_tf.id, req_bad_tf1, clock)
    assert exc.value.status_code == 422
    assert exc.value.code == "invalid_answer_schema"

    # 4. TF with invalid statement id
    req_bad_tf2 = StudentSaveAnswerRequest(value={"statements": {"s99": True}}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_tf.id, req_bad_tf2, clock)
    assert exc.value.status_code == 422
    assert exc.value.code == "invalid_answer_schema"

    # 5. Short number with unparseable text
    req_bad_num = StudentSaveAnswerRequest(value={"value": "khong_phai_so"}, client_seq=1)
    with pytest.raises(AppError) as exc:
        save_student_answer(session, student, attempt.id, q_num.id, req_bad_num, clock)
    assert exc.value.status_code == 422
    assert exc.value.code == "invalid_answer_schema"


# ==============================================================================
# TC-5.4-07: Saved Answer Persisted and Retained for Grading
# ==============================================================================
def test_tc_5_4_07_saved_answer_persisted_for_grading(test_db_session):
    """TC-5.4-07: Answer successfully saved before submission is guaranteed intact in DB."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_07", role="admin")
    student = create_test_user(session, "student_54_07", role="student")
    exam = create_test_exam(session, admin.id)
    q1 = create_test_question(session, exam.id, 1, "mcq")
    q2 = create_test_question(session, exam.id, 2, "tf")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # Save answers
    res1 = save_student_answer(
        session,
        student,
        attempt.id,
        q1.id,
        StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1),
        clock,
    )
    assert res1.status == "saved"

    res2 = save_student_answer(
        session,
        student,
        attempt.id,
        q2.id,
        StudentSaveAnswerRequest(value={"statements": {"s1": True, "s2": False}}, client_seq=1),
        clock,
    )
    assert res2.status == "saved"

    # Simulate submission
    attempt.status = "submitted"
    attempt.submitted_at = now + timedelta(minutes=30)
    session.commit()

    # Verify answers exist in DB intact
    answers = session.scalars(
        select(Answer).where(Answer.attempt_id == attempt.id).order_by(Answer.updated_at.asc())
    ).all()
    assert len(answers) == 2

    ans_map = {a.question_id: a.value for a in answers}
    assert ans_map[q1.id] == {"selected": "o1"}
    assert ans_map[q2.id] == {"statements": {"s1": True, "s2": False}}


# ==============================================================================
# TC-5.4-08: Concurrent Saves of Different Questions Parallel via FOR SHARE
# ==============================================================================
def test_tc_5_4_08_concurrent_save_different_questions_sqlite(test_db_session):
    """TC-5.4-08: Sequential & concurrent saves of different questions do not collide."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_54_08", role="admin")
    student = create_test_user(session, "student_54_08", role="student")
    exam = create_test_exam(session, admin.id)
    q1 = create_test_question(session, exam.id, 1, "mcq")
    q2 = create_test_question(session, exam.id, 2, "mcq")

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    res1 = save_student_answer(
        session,
        student,
        attempt.id,
        q1.id,
        StudentSaveAnswerRequest(value={"selected": "o1"}, client_seq=1),
        clock,
    )
    res2 = save_student_answer(
        session,
        student,
        attempt.id,
        q2.id,
        StudentSaveAnswerRequest(value={"selected": "o2"}, client_seq=1),
        clock,
    )

    assert res1.status == "saved"
    assert res2.status == "saved"

    db_answers = session.scalars(select(Answer).where(Answer.attempt_id == attempt.id)).all()
    assert len(db_answers) == 2


def test_tc_5_4_08_concurrent_save_postgres():
    """TC-5.4-08: Concurrency test on real PostgreSQL:

    Two concurrent worker threads each save a different question in the same attempt.
    Both run SELECT ... FOR SHARE on the attempt row simultaneously without deadlock.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL not reachable for concurrency test: {exc}")

    with Session(engine) as session:
        admin = create_test_user(session, f"admin_tc54_{uuid.uuid4().hex[:6]}", role="admin")
        student = create_test_user(session, f"student_tc54_{uuid.uuid4().hex[:6]}", role="student")
        exam = create_test_exam(session, admin.id, title="Đề Concurrency FOR SHARE 5.4")
        q1 = create_test_question(session, exam.id, 1, "mcq")
        q2 = create_test_question(session, exam.id, 2, "mcq")

        attempt = Attempt(
            id=uuid.uuid4(),
            exam_id=exam.id,
            student_id=student.id,
            status="in_progress",
            started_at=datetime.now(UTC),
            deadline_at=datetime.now(UTC) + timedelta(minutes=45),
            shuffle_seed=99999,
        )
        session.add(attempt)
        session.commit()

        attempt_id = attempt.id
        q1_id = q1.id
        q2_id = q2.id
        student_id = student.id

    def worker_save(question_id: uuid.UUID, opt_id: str):
        with Session(engine) as worker_session:
            worker_student = worker_session.get(User, student_id)
            clock = FakeClock(datetime.now(UTC))
            req = StudentSaveAnswerRequest(value={"selected": opt_id}, client_seq=1)
            return save_student_answer(
                worker_session, worker_student, attempt_id, question_id, req, clock
            )

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(worker_save, q1_id, "o1")
        f2 = executor.submit(worker_save, q2_id, "o2")

        res1 = f1.result(timeout=10)
        res2 = f2.result(timeout=10)

    assert res1.status == "saved"
    assert res2.status == "saved"

    with Session(engine) as verify_session:
        saved_count = verify_session.scalars(
            select(Answer).where(Answer.attempt_id == attempt_id)
        ).all()
        assert len(saved_count) == 2
