"""Unit and Integration Tests for Step 5.5: Attempt Status Endpoint & Monotonic Clock Sync.

Test Cases:
- TC-5.5-BE-01: Status sync returns accurate remaining_seconds and server_now
- TC-5.5-BE-02: Security isolation: cross-student returns 404, inactive returns 403
- TC-5.5-BE-03: Submitted attempt returns status="submitted" and remaining_seconds=0
- TC-5.5-BE-04: Expired attempt (past deadline + 10s grace) lazily finalizes to submitted
- TC-5.5-BE-05: Extended deadline reflects immediately in remaining_seconds (TC-5.5-05)
- TC-5.5-BE-06: Ultra-low bandwidth payload (< 1 KB) and <= 1 SQL query (TC-5.5-06)
"""

import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from app.core.errors import AppError
from app.core.time import FakeClock
from app.db.base import Base
from app.models import Attempt, Exam, User
from app.schemas.student_exam_schema import StudentAttemptStatusResponse
from app.services.student_exam_service import get_student_attempt_status


def create_test_user(
    session: Session,
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


def create_test_exam(session: Session, admin_id: uuid.UUID, title: str = "Đề Kiểm Tra") -> Exam:
    exam = Exam(
        id=uuid.uuid4(),
        title=title,
        subject="toan",
        duration_minutes=45,
        status="published",
        created_by=admin_id,
    )
    session.add(exam)
    session.flush()
    return exam


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
# TC-5.5-BE-01: Status sync returns accurate remaining_seconds and server_now
# ==============================================================================
def test_tc_5_5_be_01_status_sync_accuracy(test_db_session):
    """TC-5.5-BE-01: Status endpoint accurately calculates remaining seconds."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_01", role="admin")
    student = create_test_user(session, "student_55_01", role="student")
    exam = create_test_exam(session, admin.id)

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

    res = get_student_attempt_status(session, student, attempt.id, clock)
    assert isinstance(res, StudentAttemptStatusResponse)
    assert res.id == attempt.id
    assert res.status == "in_progress"
    assert res.remaining_seconds == 45 * 60  # 2700 seconds
    assert res.submitted_at is None

    # Advance clock by 10 minutes and 30 seconds (630 seconds)
    clock.advance(seconds=630)
    res2 = get_student_attempt_status(session, student, attempt.id, clock)
    assert res2.remaining_seconds == 2700 - 630  # 2070 seconds


# ==============================================================================
# TC-5.5-BE-02: Security isolation: cross-student returns 404, inactive returns 403
# ==============================================================================
def test_tc_5_5_be_02_security_isolation(test_db_session):
    """TC-5.5-BE-02: Non-owner gets 404 attempt_not_found; inactive gets 403."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_02", role="admin")
    student_a = create_test_user(session, "student_55_02_a", role="student")
    student_b = create_test_user(session, "student_55_02_b", role="student")
    student_inactive = create_test_user(session, "student_55_02_c", role="student", is_active=False)
    exam = create_test_exam(session, admin.id)

    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_a.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    # Student B queries Student A's attempt -> 404 (anti-enumeration)
    with pytest.raises(AppError) as exc_404:
        get_student_attempt_status(session, student_b, attempt.id, clock)
    assert exc_404.value.status_code == 404
    assert exc_404.value.code == "attempt_not_found"

    # Inactive student queries own attempt -> 403 inactive_account
    attempt_inactive = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_inactive.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=54321,
    )
    session.add(attempt_inactive)
    session.commit()

    with pytest.raises(AppError) as exc_403:
        get_student_attempt_status(session, student_inactive, attempt_inactive.id, clock)
    assert exc_403.value.status_code == 403
    assert exc_403.value.code == "inactive_account"


# ==============================================================================
# TC-5.5-BE-03: Submitted attempt returns status="submitted" & remaining_seconds=0
# ==============================================================================
def test_tc_5_5_be_03_submitted_attempt(test_db_session):
    """TC-5.5-BE-03: Already submitted attempt returns status=submitted and 0 remaining."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_03", role="admin")
    student = create_test_user(session, "student_55_03", role="student")
    exam = create_test_exam(session, admin.id)

    submitted_time = now - timedelta(minutes=5)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="submitted",
        started_at=now - timedelta(minutes=30),
        deadline_at=now + timedelta(minutes=15),
        submitted_at=submitted_time,
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    res = get_student_attempt_status(session, student, attempt.id, clock)
    assert res.status == "submitted"
    assert res.remaining_seconds == 0
    assert res.submitted_at.replace(tzinfo=UTC) == submitted_time


# ==============================================================================
# TC-5.5-BE-04: Expired attempt lazily finalizes to submitted
# ==============================================================================
def test_tc_5_5_be_04_expired_lazy_finalize(test_db_session):
    """TC-5.5-BE-04: Attempt past deadline + 10s grace is lazily marked submitted."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_04", role="admin")
    student = create_test_user(session, "student_55_04", role="student")
    exam = create_test_exam(session, admin.id)

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

    # Advance clock past deadline + 10s grace
    clock.advance(seconds=45 * 60 + 11)

    res = get_student_attempt_status(session, student, attempt.id, clock)
    assert res.status == "submitted"
    assert res.remaining_seconds == 0
    assert res.submitted_at.replace(tzinfo=UTC) == deadline

    # Verify committed DB status
    session.refresh(attempt)
    assert attempt.status == "submitted"
    assert attempt.submitted_at.replace(tzinfo=UTC) == deadline


# ==============================================================================
# TC-5.5-BE-05: Extended deadline reflects immediately in remaining_seconds
# ==============================================================================
def test_tc_5_5_be_05_deadline_extension_reflection(test_db_session):
    """TC-5.5-BE-05: When teacher extends deadline, next status sync updates remaining_seconds."""
    session, _ = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_05", role="admin")
    student = create_test_user(session, "student_55_05", role="student")
    exam = create_test_exam(session, admin.id)

    original_deadline = now + timedelta(minutes=10)
    attempt = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=original_deadline,
        shuffle_seed=12345,
    )
    session.add(attempt)
    session.commit()

    res1 = get_student_attempt_status(session, student, attempt.id, clock)
    assert res1.remaining_seconds == 600

    # Teacher extends deadline by +300 seconds (5 minutes)
    extended_deadline = original_deadline + timedelta(seconds=300)
    attempt.deadline_at = extended_deadline
    session.commit()

    res2 = get_student_attempt_status(session, student, attempt.id, clock)
    assert res2.remaining_seconds == 900
    assert res2.deadline_at.replace(tzinfo=UTC) == extended_deadline


# ==============================================================================
# TC-5.5-BE-06: Ultra-low bandwidth payload (< 1 KB) & <= 1 SQL query (TC-5.5-06)
# ==============================================================================
def test_tc_5_5_be_06_payload_size_and_sql_budget(test_db_session):
    """TC-5.5-BE-06: Status sync executes exactly 1 SQL query and payload is < 1 KB."""
    session, engine = test_db_session
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    admin = create_test_user(session, "admin_55_06", role="admin")
    student = create_test_user(session, "student_55_06", role="student")
    exam = create_test_exam(session, admin.id)

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

    attempt_id = attempt.id
    session.refresh(student)

    # 1. Statement Budget Check (<= 1 query)
    statements = []

    def count_sql(conn, cursor, statement, parameters, context, executemany):
        statements.append(statement)

    event.listen(engine, "before_cursor_execute", count_sql)
    try:
        res = get_student_attempt_status(session, student, attempt_id, clock)
    finally:
        event.remove(engine, "before_cursor_execute", count_sql)

    assert len(statements) <= 1, f"Expected <= 1 query, executed: {len(statements)}"

    # 2. Payload size check (< 1 KB)
    json_bytes = json.dumps(res.model_dump(), default=str).encode("utf-8")
    payload_size = len(json_bytes)
    assert payload_size < 1024, f"Payload size {payload_size} bytes exceeds 1 KB"
    assert payload_size < 300, f"Payload size {payload_size} bytes unexpectedly large"
