"""Unit and Integration Tests for Step 5.3: Load/Resume Exam Attempt & Deterministic Shuffling.

Test Cases:
- TC-5.3-01: Deterministic shuffle stability across multiple reloads (same seed = same order)
- TC-5.3-02: Inter-student shuffle variance (different seeds = different question/option order)
- TC-5.3-03: Recursive scan of attempt detail guarantees 0% answer or scoring data leakage
- TC-5.3-04: Student ownership isolation: Student A accessing Student B's attempt returns 404
- TC-5.3-05: Tab resume with saved answers: all answered questions returned with client_seq
- TC-5.3-06: Lazy finalization: attempt past deadline + grace auto-submits
- TC-5.3-07: Real-time remaining_seconds precision down to the exact second
- TC-5.3-08: Query budget optimization: loading 60 questions with 10 images executes <= 4 queries
- TC-5.3-09: Resilient corrupt question handling: corrupt config marked unavailable without crashing
"""

import json
import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.errors import AppError
from app.core.time import FakeClock
from app.db.base import Base
from app.models import Answer, Attempt, Exam, File, Question, User
from app.services.student_exam_service import get_student_attempt_detail

FORBIDDEN_STUDENT_KEYS = {
    "total_score",
    "score",
    "score_total",
    "answer_key",
    "correct",
    "accepted",
    "values",
    "tolerance",
    "explanation",
    "explanation_md",
    "sub_scores",
    "feedback_md",
    "result_visibility",
}


def recursive_find_keys(obj: Any) -> set[str]:
    """Recursively collects all dictionary keys at any depth in a JSON object."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys.update(recursive_find_keys(v))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(recursive_find_keys(item))
    return keys


def create_test_user(
    session,
    username: str,
    role: str = "student",
    full_name: str = "Test User",
    is_active: bool = True,
) -> User:
    """Helper creating user with required hashed_password."""
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


def test_tc_5_3_01_deterministic_shuffle_reloads(test_db_session):
    """TC-5.3-01: Deterministic shuffle stability: multiple loads return identical order."""
    session, _ = test_db_session

    student = create_test_user(
        session, "student_tc53_01", role="student", full_name="Student 53-01"
    )
    admin = create_test_user(session, "admin_tc53_01", role="admin", full_name="Admin 53-01")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Xáo Trộn Ổn Định",
        subject="toan",
        duration_minutes=45,
        status="published",
        shuffle_questions=True,
        shuffle_options=True,
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    # Create 5 MCQ questions
    for i in range(1, 6):
        q = Question(
            id=uuid.uuid4(),
            exam_id=exam.id,
            position=i,
            question_type="mcq",
            content_md=f"Câu hỏi số {i}?",
            config={
                "options": [
                    {"id": f"opt_{i}_a", "content_md": f"Lựa chọn {i}-A"},
                    {"id": f"opt_{i}_b", "content_md": f"Lựa chọn {i}-B"},
                    {"id": f"opt_{i}_c", "content_md": f"Lựa chọn {i}-C"},
                    {"id": f"opt_{i}_d", "content_md": f"Lựa chọn {i}-D"},
                ]
            },
            answer_key={"correct": f"opt_{i}_a"},
            points=Decimal("2.00"),
        )
        session.add(q)

    # Attempt with fixed seed
    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=987654321,
    )
    session.add(attempt)
    session.commit()

    clock = FakeClock(now)

    # 1st call
    res1 = get_student_attempt_detail(session, student, attempt.id, clock)
    # 2nd call
    res2 = get_student_attempt_detail(session, student, attempt.id, clock)
    # 3rd call
    res3 = get_student_attempt_detail(session, student, attempt.id, clock)

    # Verify questions order is 100% identical across all 3 calls
    q_ids_1 = [q["id"] for q in res1.questions]
    q_ids_2 = [q["id"] for q in res2.questions]
    q_ids_3 = [q["id"] for q in res3.questions]
    assert q_ids_1 == q_ids_2 == q_ids_3

    # Verify option order for each question is 100% identical across all 3 calls
    for q1, q2, q3 in zip(res1.questions, res2.questions, res3.questions, strict=True):
        opts_1 = [o["id"] for o in q1["config"]["options"]]
        opts_2 = [o["id"] for o in q2["config"]["options"]]
        opts_3 = [o["id"] for o in q3["config"]["options"]]
        assert opts_1 == opts_2 == opts_3


def test_tc_5_3_02_different_students_receive_different_orders(test_db_session):
    """TC-5.3-02: Different students with different seeds receive distinct orders."""
    session, _ = test_db_session

    student_a = create_test_user(session, "student_a", role="student", full_name="Student A")
    student_b = create_test_user(session, "student_b", role="student", full_name="Student B")
    admin = create_test_user(session, "admin_ab", role="admin", full_name="Admin AB")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi 10 Câu Xáo Trộn",
        subject="tin",
        duration_minutes=30,
        status="published",
        shuffle_questions=True,
        shuffle_options=True,
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    for i in range(1, 11):
        q = Question(
            id=uuid.uuid4(),
            exam_id=exam.id,
            position=i,
            question_type="mcq",
            content_md=f"Câu hỏi số {i} nội dung tin học?",
            config={
                "options": [
                    {"id": f"opt_{i}_1", "content_md": f"Option {i}-1"},
                    {"id": f"opt_{i}_2", "content_md": f"Option {i}-2"},
                    {"id": f"opt_{i}_3", "content_md": f"Option {i}-3"},
                    {"id": f"opt_{i}_4", "content_md": f"Option {i}-4"},
                ]
            },
            answer_key={"correct": f"opt_{i}_1"},
            points=Decimal("1.00"),
        )
        session.add(q)

    now = datetime(2026, 11, 18, 9, 0, 0, tzinfo=UTC)
    attempt_a = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_a.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=30),
        shuffle_seed=111111111,
    )
    attempt_b = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_b.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=30),
        shuffle_seed=999999999,
    )
    session.add_all([attempt_a, attempt_b])
    session.commit()

    clock = FakeClock(now)
    res_a = get_student_attempt_detail(session, student_a, attempt_a.id, clock)
    res_b = get_student_attempt_detail(session, student_b, attempt_b.id, clock)

    # 1. Question order must differ between student A and student B
    q_ids_a = [q["id"] for q in res_a.questions]
    q_ids_b = [q["id"] for q in res_b.questions]
    assert q_ids_a != q_ids_b

    # 2. Both students still receive all 10 questions
    assert set(q_ids_a) == set(q_ids_b)
    assert len(q_ids_a) == 10


def test_tc_5_3_03_zero_answer_leakage_scan(test_db_session):
    """TC-5.3-03: Recursive scan of attempt detail guarantees 0% answer or scoring data leakage."""
    session, _ = test_db_session

    student = create_test_user(session, "student_sec", role="student", full_name="Student Sec")
    admin = create_test_user(session, "admin_sec", role="admin", full_name="Admin Sec")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Bảo Mật",
        subject="toan",
        duration_minutes=40,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    q_mcq = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=1,
        question_type="mcq",
        content_md="Câu hỏi trắc nghiệm bí mật?",
        config={"options": [{"id": "a", "content_md": "A"}, {"id": "b", "content_md": "B"}]},
        answer_key={"correct": "a"},
        explanation_md="Giải thích đáp án bí mật A đúng",
        points=Decimal("5.00"),
    )
    q_num = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=2,
        question_type="short_number",
        content_md="Tính tích phân?",
        config={"precision": 2},
        answer_key={"correct_value": 3.14, "tolerance": 0.01},
        explanation_md="Giải thích bí mật số pi",
        points=Decimal("5.00"),
    )
    session.add_all([q_mcq, q_num])

    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=40),
        shuffle_seed=424242,
    )
    session.add(attempt)
    session.flush()

    ans = Answer(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        question_id=q_mcq.id,
        value={"selected": "a"},
        client_seq=1,
        score=Decimal("5.00"),
        is_correct=True,
        feedback_md="Rất tốt!",
    )
    session.add(ans)
    session.commit()

    clock = FakeClock(now)
    response = get_student_attempt_detail(session, student, attempt.id, clock)
    data = response.model_dump()

    # Scan all keys at any nesting depth
    leaked_keys = recursive_find_keys(data).intersection(FORBIDDEN_STUDENT_KEYS)
    assert not leaked_keys, f"Security violation: Sensitive keys leaked to student: {leaked_keys}"

    # Verify explanation strings are completely omitted
    raw_json = json.dumps(data, default=str)
    assert "Giải thích đáp án bí mật" not in raw_json
    assert "Giải thích bí mật số pi" not in raw_json


def test_tc_5_3_04_ownership_isolation_cross_student_returns_404(test_db_session):
    """TC-5.3-04: Student A accessing Student B's attempt returns 404 attempt_not_found."""
    session, _ = test_db_session

    student_a = create_test_user(session, "student_a_own", role="student", full_name="Student A")
    student_b = create_test_user(session, "student_b_own", role="student", full_name="Student B")
    admin = create_test_user(session, "admin_own", role="admin", full_name="Admin Own")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Quyền Sở Hữu",
        subject="both",
        duration_minutes=30,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt_b = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_b.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=30),
        shuffle_seed=555555,
    )
    session.add(attempt_b)
    session.commit()

    clock = FakeClock(now)

    # Student A attempts to access Student B's attempt ID
    with pytest.raises(AppError) as exc_info:
        get_student_attempt_detail(session, student_a, attempt_b.id, clock)

    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "attempt_not_found"

    # Non-existent attempt ID also returns 404
    with pytest.raises(AppError) as exc_info2:
        get_student_attempt_detail(session, student_a, uuid.uuid4(), clock)

    assert exc_info2.value.status_code == 404
    assert exc_info2.value.code == "attempt_not_found"


def test_tc_5_3_05_resume_attempt_with_saved_answers_and_client_seq(test_db_session):
    """TC-5.3-05: Closing and reopening attempt restores all saved answers along with client_seq."""
    session, _ = test_db_session

    student = create_test_user(
        session, "student_resume", role="student", full_name="Student Resume"
    )
    admin = create_test_user(session, "admin_resume", role="admin", full_name="Admin Resume")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Tiếp Tục Làm",
        subject="toan",
        duration_minutes=45,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    q1 = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=1,
        question_type="mcq",
        content_md="Câu 1?",
        config={"options": [{"id": "opt1", "content_md": "1"}, {"id": "opt2", "content_md": "2"}]},
        points=Decimal("5.00"),
    )
    q2 = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=2,
        question_type="short_text",
        content_md="Câu 2?",
        config={"max_length": 50},
        points=Decimal("5.00"),
    )
    session.add_all([q1, q2])

    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=777777,
    )
    session.add(attempt)
    session.flush()

    # Save answers for q1 and q2 with explicit client_seq
    ans1 = Answer(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        question_id=q1.id,
        value={"selected": "opt2"},
        client_seq=10,
    )
    ans2 = Answer(
        id=uuid.uuid4(),
        attempt_id=attempt.id,
        question_id=q2.id,
        value={"text": "Cau tra loi hoc sinh"},
        client_seq=25,
    )
    session.add_all([ans1, ans2])
    session.commit()

    clock = FakeClock(now)
    res = get_student_attempt_detail(session, student, attempt.id, clock)

    assert str(q1.id) in res.answers
    assert str(q2.id) in res.answers

    assert res.answers[str(q1.id)].value == {"selected": "opt2"}
    assert res.answers[str(q1.id)].client_seq == 10

    assert res.answers[str(q2.id)].value == {"text": "Cau tra loi hoc sinh"}
    assert res.answers[str(q2.id)].client_seq == 25


def test_tc_5_3_06_lazy_finalization_past_deadline_plus_grace(test_db_session):
    """TC-5.3-06: Loading an attempt past deadline + grace auto-finalizes to submitted."""
    session, _ = test_db_session

    student = create_test_user(session, "student_lazy", role="student", full_name="Student Lazy")
    admin = create_test_user(session, "admin_lazy", role="admin", full_name="Admin Lazy")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Quá Hạn",
        subject="toan",
        duration_minutes=30,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    start_time = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    deadline_time = start_time + timedelta(minutes=30)  # 8:30:00

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=start_time,
        deadline_at=deadline_time,
        shuffle_seed=888888,
    )
    session.add(attempt)
    session.commit()

    # Time is now 8:30:15 (15 seconds after deadline -> past 10s grace)
    clock = FakeClock(deadline_time + timedelta(seconds=15))
    res = get_student_attempt_detail(session, student, attempt.id, clock)

    assert res.status == "submitted"
    assert res.remaining_seconds == 0
    assert res.submitted_at == deadline_time

    # Verify attempt in DB was persisted as submitted
    db_attempt = session.get(Attempt, attempt.id)
    assert db_attempt.status == "submitted"
    assert db_attempt.submitted_at.replace(tzinfo=UTC) == deadline_time


def test_tc_5_3_07_remaining_seconds_precision(test_db_session):
    """TC-5.3-07: Remaining seconds precision down to the exact second."""
    session, _ = test_db_session

    student = create_test_user(session, "student_rem", role="student", full_name="Student Rem")
    admin = create_test_user(session, "admin_rem", role="admin", full_name="Admin Rem")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Đếm Ngược",
        subject="both",
        duration_minutes=60,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    start_time = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    deadline_time = start_time + timedelta(minutes=60)  # 11:00:00

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=start_time,
        deadline_at=deadline_time,
        shuffle_seed=333333,
    )
    session.add(attempt)
    session.commit()

    # 1. 20 minutes elapsed -> 40 minutes (2400s) left
    clock1 = FakeClock(start_time + timedelta(minutes=20))
    res1 = get_student_attempt_detail(session, student, attempt.id, clock1)
    assert res1.remaining_seconds == 2400

    # 2. 59 minutes and 15 seconds elapsed -> 45 seconds left
    clock2 = FakeClock(start_time + timedelta(minutes=59, seconds=15))
    res2 = get_student_attempt_detail(session, student, attempt.id, clock2)
    assert res2.remaining_seconds == 45

    # 3. Exactly at deadline -> 0 seconds left
    clock3 = FakeClock(deadline_time)
    res3 = get_student_attempt_detail(session, student, attempt.id, clock3)
    assert res3.remaining_seconds == 0


def test_tc_5_3_08_sql_statement_budget_max_four_queries(test_db_session):
    """TC-5.3-08: Loading 60 questions with 10 images executes <= 4 SQL queries."""
    session, engine = test_db_session

    student = create_test_user(session, "student_opt", role="student", full_name="Student Opt")
    admin = create_test_user(session, "admin_opt", role="admin", full_name="Admin Opt")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi 60 Câu Tối Ưu SQL",
        subject="toan",
        duration_minutes=90,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    # Create 10 image files owned by this exam
    file_ids = [uuid.uuid4() for _ in range(10)]
    for fid in file_ids:
        f = File(
            id=fid,
            exam_id=exam.id,
            s3_key=f"exams/{exam.id}/img/{fid}.webp",
            original_name=f"img_{fid}.webp",
            mime_type="image/webp",
            size_bytes=1024,
            user_id=admin.id,
        )
        session.add(f)
    session.flush()

    # Create 60 questions (first 10 have images: asset:<uuid>)
    for i in range(1, 61):
        if i <= 10:
            content = f"Câu hỏi {i} có hình ảnh minh họa: ![Hinh](asset:{file_ids[i - 1]})"
        else:
            content = f"Câu hỏi {i} nội dung dạng văn bản thuần túy."

        q = Question(
            id=uuid.uuid4(),
            exam_id=exam.id,
            position=i,
            question_type="mcq",
            content_md=content,
            config={
                "options": [
                    {"id": "opt_a", "content_md": "Phương án A"},
                    {"id": "opt_b", "content_md": "Phương án B"},
                ]
            },
            points=Decimal("1.00"),
        )
        session.add(q)

    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=90),
        shuffle_seed=444444,
    )
    session.add(attempt)
    session.commit()

    attempt_id = attempt.id

    # Refresh student attributes so accessing user.is_active doesn't reload
    session.refresh(student)

    # Attach SQL statement counter listener
    sql_statements = []

    def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
        sql_statements.append(statement)

    event.listen(engine, "before_cursor_execute", before_cursor_execute)

    clock = FakeClock(now)
    try:
        res = get_student_attempt_detail(session, student, attempt_id, clock)
    finally:
        event.remove(engine, "before_cursor_execute", before_cursor_execute)

    # Verify query count budget is strictly <= 4 queries
    assert len(sql_statements) <= 4, (
        f"Exceeded SQL statement budget: executed {len(sql_statements)} statements (max allowed: 4)"
    )

    # Verify that all 60 questions loaded and images were resolved
    assert len(res.questions) == 60
    for i in range(10):
        q_item = res.questions[i]
        assert "asset:" not in q_item["content_md"]
        assert "http" in q_item["content_md"] or "quiz-files" in q_item["content_md"]


def test_tc_5_3_09_corrupt_question_returns_unavailable_safe(test_db_session):
    """TC-5.3-09: Corrupt question configuration in DB returns unavailable: True safely."""
    session, _ = test_db_session

    student = create_test_user(
        session, "student_corrupt", role="student", full_name="Student Corrupt"
    )
    admin = create_test_user(session, "admin_corrupt", role="admin", full_name="Admin Corrupt")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Có Câu Hỏng",
        subject="tin",
        duration_minutes=30,
        status="published",
        created_by=admin.id,
    )
    session.add(exam)
    session.flush()

    # Valid question
    q_valid = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=1,
        question_type="mcq",
        content_md="Câu hỏi hợp lệ?",
        config={"options": [{"id": "1", "content_md": "OK 1"}, {"id": "2", "content_md": "OK 2"}]},
        points=Decimal("5.00"),
    )

    # Corrupt question (MCQ with empty options list in config)
    q_corrupt = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=2,
        question_type="mcq",
        content_md="Câu hỏi bị hỏng dữ liệu config?",
        config={"options": []},  # Invalid for MCQ
        points=Decimal("5.00"),
    )
    session.add_all([q_valid, q_corrupt])

    now = datetime(2026, 11, 18, 8, 0, 0, tzinfo=UTC)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=30),
        shuffle_seed=666666,
    )
    session.add(attempt)
    session.commit()

    clock = FakeClock(now)
    res = get_student_attempt_detail(session, student, attempt.id, clock)

    assert len(res.questions) == 2

    # Find the corrupt question in the response
    corrupt_item = next(q for q in res.questions if q["id"] == str(q_corrupt.id))
    assert corrupt_item["unavailable"] is True
    assert corrupt_item["config"] == {}

    # Valid question should be normal
    valid_item = next(q for q in res.questions if q["id"] == str(q_valid.id))
    assert valid_item.get("unavailable", False) is False
    assert len(valid_item["config"]["options"]) == 2
