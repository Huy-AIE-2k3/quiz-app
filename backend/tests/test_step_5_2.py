"""Unit and Concurrency Integration Tests for Step 5.2: Start Exam Attempt.

Test Cases:
- TC-5.2-01: Standard attempt start, deadline calculation, and exam content locking
- TC-5.2-02: 10 concurrent threads on PostgreSQL create exactly 1 attempt (ON CONFLICT)
- TC-5.2-03: Multi-device race condition: same attempt_id, started_at, deadline_at
- TC-5.2-04: Time window enforcement: before open, at open, near close, after close
- TC-5.2-05: Access control: non-enrolled student gets 404, inactive student gets 403
- TC-5.2-06: Idempotent resume: submitted attempt returns submitted without new attempt
- TC-5.2-07: Lazy finalization: expired attempt (now >= deadline + grace) marks submitted
- TC-5.2-08: Content locking is immutable: second student does not overwrite locked_at
- TC-5.2-09: Unpublished exam: calling start on draft or archived exam returns 404
"""

import concurrent.futures
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.time import FakeClock
from app.db.session import get_engine
from app.models import Attempt, Class, Exam, ExamClass, User
from app.models.class_model import ClassMember
from app.services.student_exam_service import start_student_attempt


class MockDBStep52:
    """Mock database session for Step 5.2 unit testing."""

    def __init__(
        self,
        exam: Exam | None = None,
        attempts: list[Attempt] | None = None,
        is_enrolled: bool = True,
    ):
        self.exam = exam
        self._attempts = attempts or []
        self._is_enrolled = is_enrolled
        self.bind = None

    def get(self, model, ident):
        if model is Exam and self.exam and self.exam.id == ident:
            return self.exam
        if model is Attempt:
            for att in self._attempts:
                if att.id == ident:
                    return att
        return None

    def scalar(self, query):
        q_str = str(query).lower()
        if "from attempts" in q_str:
            return self._attempts[0] if self._attempts else None
        if "class_members" in q_str:
            return uuid.uuid4() if self._is_enrolled else None
        return None

    def execute(self, query):
        q_str = str(query).lower()
        params = query.compile().params if hasattr(query, "compile") else {}
        if "insert into attempts" in q_str:
            # If attempt already exists, on conflict do nothing returns None
            if self._attempts:
                return self._row_result([])
            new_id = uuid.uuid4()
            started_at = params.get("started_at", datetime.now(UTC))
            deadline_at = params.get("deadline_at", datetime.now(UTC) + timedelta(minutes=45))
            mock_att = Attempt(
                id=new_id,
                exam_id=self.exam.id,
                student_id=uuid.uuid4(),
                status="in_progress",
                started_at=started_at,
                deadline_at=deadline_at,
                shuffle_seed=123,
            )
            self._attempts.append(mock_att)
            return self._row_result([(new_id,)])

        if "update exams" in q_str:
            locked_at = params.get("locked_at", datetime.now(UTC))
            if self.exam and self.exam.locked_at is None:
                self.exam.locked_at = locked_at
            return self._row_result([])

        return self._row_result([])

    def _row_result(self, rows):
        class RowResult:
            def __init__(self, data):
                self._data = data

            def first(self):
                return self._data[0] if self._data else None

            def all(self):
                return self._data

        return RowResult(rows)

    def commit(self):
        pass

    def refresh(self, obj):
        pass


# ==============================================================================
# TC-5.2-01: Standard Attempt Start, Deadline Calculation & Content Lock
# ==============================================================================
def test_tc_5_2_01_standard_start_and_lock():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi 45 Phút",
        subject="toan",
        duration_minutes=45,
        status="published",
        locked_at=None,
        created_by=admin_id,
    )
    student = User(
        id=student_id,
        username="student1",
        full_name="Học Sinh 1",
        role="student",
        is_active=True,
    )

    db = MockDBStep52(exam=exam, is_enrolled=True)
    res = start_student_attempt(db, student, exam.id, clock)

    assert res.status == "in_progress"
    assert res.started_at == now
    assert res.deadline_at == now + timedelta(minutes=45)
    assert res.remaining_seconds == 45 * 60
    assert exam.locked_at is not None


# ==============================================================================
# TC-5.2-03: Multi-device Race Condition: Same Attempt Returned
# ==============================================================================
def test_tc_5_2_03_multi_device_same_attempt():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi 45 Phút",
        subject="toan",
        duration_minutes=45,
        status="published",
        locked_at=now,
        created_by=admin_id,
    )
    student = User(
        id=student_id,
        username="student1",
        full_name="Học Sinh 1",
        role="student",
        is_active=True,
    )
    existing_att = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=999,
    )

    db = MockDBStep52(exam=exam, attempts=[existing_att], is_enrolled=True)
    res1 = start_student_attempt(db, student, exam.id, clock)
    res2 = start_student_attempt(db, student, exam.id, clock)

    assert res1.id == existing_att.id
    assert res2.id == existing_att.id
    assert res1.deadline_at == res2.deadline_at


# ==============================================================================
# TC-5.2-04: Time Window Enforcement (before open, at open, near close, after close)
# ==============================================================================
def test_tc_5_2_04_time_window_enforcement():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    base = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(base)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Có Khung Giờ",
        subject="toan",
        duration_minutes=60,
        status="published",
        open_at=base + timedelta(hours=1),  # 11:00
        close_at=base + timedelta(hours=3),  # 13:00
        created_by=admin_id,
    )
    student = User(
        id=student_id,
        username="student1",
        full_name="Học Sinh 1",
        role="student",
        is_active=True,
    )

    db = MockDBStep52(exam=exam, is_enrolled=True)

    # 1. Before open_at (10:59) -> 409 exam_not_open
    clock.set_time(base + timedelta(minutes=59))
    with pytest.raises(AppError) as exc_before:
        start_student_attempt(db, student, exam.id, clock)
    assert exc_before.value.status_code == 409
    assert exc_before.value.code == "exam_not_open"

    # 2. Exactly at open_at (11:00) -> 200
    clock.set_time(base + timedelta(hours=1))
    db._attempts = []
    res_open = start_student_attempt(db, student, exam.id, clock)
    assert res_open.status == "in_progress"
    assert res_open.deadline_at == base + timedelta(hours=2)  # 11:00 + 60m = 12:00 <= 13:00

    # 3. Near close_at: only 1 second left before close_at (12:59:59)
    # Deadline cannot exceed close_at -> deadline = 13:00 (1 second remaining)
    clock.set_time(base + timedelta(hours=2, minutes=59, seconds=59))
    db._attempts = []
    res_near_close = start_student_attempt(db, student, exam.id, clock)
    assert res_near_close.deadline_at == exam.close_at
    assert res_near_close.remaining_seconds == 1

    # 4. After close_at (13:00:01) -> 409 exam_closed
    clock.set_time(base + timedelta(hours=3, seconds=1))
    db._attempts = []
    with pytest.raises(AppError) as exc_closed:
        start_student_attempt(db, student, exam.id, clock)
    assert exc_closed.value.status_code == 409
    assert exc_closed.value.code == "exam_closed"


# ==============================================================================
# TC-5.2-05: Access Control (Not Enrolled -> 404, Inactive Account -> 403)
# ==============================================================================
def test_tc_5_2_05_access_control():
    admin_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Bảo Vệ",
        subject="toan",
        duration_minutes=45,
        status="published",
        created_by=admin_id,
    )

    # 1. Student not enrolled in class -> 404 exam_not_found
    student_not_enrolled = User(
        id=uuid.uuid4(),
        username="outsider",
        full_name="Người Ngoài",
        role="student",
        is_active=True,
    )
    db_not_enrolled = MockDBStep52(exam=exam, is_enrolled=False)
    with pytest.raises(AppError) as exc_404:
        start_student_attempt(db_not_enrolled, student_not_enrolled, exam.id, clock)
    assert exc_404.value.status_code == 404
    assert exc_404.value.code == "exam_not_found"

    # 2. Inactive student account -> 403 inactive_account
    student_inactive = User(
        id=uuid.uuid4(),
        username="locked_user",
        full_name="Tài Khoản Khóa",
        role="student",
        is_active=False,
    )
    db_active = MockDBStep52(exam=exam, is_enrolled=True)
    with pytest.raises(AppError) as exc_403:
        start_student_attempt(db_active, student_inactive, exam.id, clock)
    assert exc_403.value.status_code == 403
    assert exc_403.value.code == "inactive_account"


# ==============================================================================
# TC-5.2-06: Re-calling Start on Submitted Attempt Returns Submitted Status
# ==============================================================================
def test_tc_5_2_06_start_on_submitted_attempt():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Đã Thi",
        subject="tin",
        duration_minutes=30,
        status="published",
        created_by=admin_id,
    )
    student = User(
        id=student_id,
        username="student1",
        full_name="Học Sinh 1",
        role="student",
        is_active=True,
    )
    submitted_att = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="submitted",
        started_at=now - timedelta(minutes=30),
        deadline_at=now,
        submitted_at=now - timedelta(minutes=5),
        shuffle_seed=555,
    )

    db = MockDBStep52(exam=exam, attempts=[submitted_att], is_enrolled=True)
    res = start_student_attempt(db, student, exam.id, clock)

    assert res.status == "submitted"
    assert res.id == submitted_att.id
    assert res.submitted_at == submitted_att.submitted_at
    assert res.remaining_seconds == 0


# ==============================================================================
# TC-5.2-07: Lazy Finalization on Expired Attempt
# ==============================================================================
def test_tc_5_2_07_lazy_finalization_past_deadline():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    start_time = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    deadline_time = start_time + timedelta(minutes=45)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi 45 Phút",
        subject="toan",
        duration_minutes=45,
        status="published",
        created_by=admin_id,
    )
    student = User(
        id=student_id,
        username="student1",
        full_name="Học Sinh 1",
        role="student",
        is_active=True,
    )
    expired_att = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student.id,
        status="in_progress",
        started_at=start_time,
        deadline_at=deadline_time,
        shuffle_seed=777,
    )

    # now = deadline + grace (10s) + 1s = deadline + 11s
    now = deadline_time + timedelta(seconds=11)
    clock = FakeClock(now)

    db = MockDBStep52(exam=exam, attempts=[expired_att], is_enrolled=True)
    res = start_student_attempt(db, student, exam.id, clock)

    assert res.status == "submitted"
    assert res.submitted_at == deadline_time
    assert res.remaining_seconds == 0
    assert expired_att.status == "submitted"


# ==============================================================================
# TC-5.2-08: Content Locking is Immutable across Multiple Students
# ==============================================================================
def test_tc_5_2_08_locked_at_immutability():
    admin_id = uuid.uuid4()
    student_1 = User(id=uuid.uuid4(), username="s1", full_name="S1", role="student", is_active=True)
    student_2 = User(id=uuid.uuid4(), username="s2", full_name="S2", role="student", is_active=True)

    time_1 = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    time_2 = datetime(2026, 11, 18, 10, 5, 0, tzinfo=UTC)
    clock = FakeClock(time_1)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Chung",
        subject="toan",
        duration_minutes=45,
        status="published",
        locked_at=None,
        created_by=admin_id,
    )

    db = MockDBStep52(exam=exam, is_enrolled=True)

    # Student 1 starts at 10:00 -> locks exam at 10:00
    start_student_attempt(db, student_1, exam.id, clock)
    first_lock = exam.locked_at
    assert first_lock == time_1

    # Student 2 starts at 10:05 -> locked_at remains 10:00, not overwritten
    clock.set_time(time_2)
    db._attempts = []  # reset attempts for student 2
    start_student_attempt(db, student_2, exam.id, clock)
    assert exam.locked_at == first_lock


# ==============================================================================
# TC-5.2-09: Calling Start on Draft or Archived Exam Returns 404
# ==============================================================================
def test_tc_5_2_09_draft_or_archived_returns_404():
    admin_id = uuid.uuid4()
    student = User(id=uuid.uuid4(), username="s1", full_name="S1", role="student", is_active=True)
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(now)

    draft_exam = Exam(
        id=uuid.uuid4(), title="Draft", subject="toan", status="draft", created_by=admin_id
    )
    archived_exam = Exam(
        id=uuid.uuid4(), title="Archived", subject="toan", status="archived", created_by=admin_id
    )

    db_draft = MockDBStep52(exam=draft_exam, is_enrolled=True)
    with pytest.raises(AppError) as exc_draft:
        start_student_attempt(db_draft, student, draft_exam.id, clock)
    assert exc_draft.value.status_code == 404
    assert exc_draft.value.code == "exam_not_found"

    db_archived = MockDBStep52(exam=archived_exam, is_enrolled=True)
    with pytest.raises(AppError) as exc_archived:
        start_student_attempt(db_archived, student, archived_exam.id, clock)
    assert exc_archived.value.status_code == 404
    assert exc_archived.value.code == "exam_not_found"


# ==============================================================================
# TC-5.2-02: 10 Concurrent Threads on PostgreSQL Create Exactly 1 Attempt
# ==============================================================================
def test_tc_5_2_02_concurrent_start_postgres():
    """10 concurrent threads call start_student_attempt on real PostgreSQL:

    Guarantees:
    - Exactly 1 attempt is created.
    - All 10 threads receive the identical attempt_id.
    - Zero 500 errors or duplicate key violations.
    """
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"PostgreSQL not reachable for concurrency test: {exc}")

    with Session(engine) as session:
        # Create test admin, student, class, enrollment, and published exam
        admin = User(
            id=uuid.uuid4(),
            username=f"admin_tc52_{uuid.uuid4().hex[:6]}",
            full_name="Admin TC52",
            hashed_password="mock_hashed_password",
            role="admin",
            is_active=True,
        )
        student = User(
            id=uuid.uuid4(),
            username=f"student_tc52_{uuid.uuid4().hex[:6]}",
            full_name="Student TC52",
            hashed_password="mock_hashed_password",
            role="student",
            is_active=True,
        )
        c = Class(
            id=uuid.uuid4(),
            code=f"C52_{uuid.uuid4().hex[:6]}",
            name="Lớp Concurrency 5.2",
            subject="toan",
            academic_year=2026,
            is_archived=False,
        )
        exam = Exam(
            id=uuid.uuid4(),
            title="Đề Thi Đồng Thời 5.2",
            subject="toan",
            duration_minutes=45,
            status="published",
            created_by=admin.id,
        )
        session.add_all([admin, student, c, exam])
        session.flush()

        session.add(ClassMember(class_id=c.id, student_id=student.id))
        session.add(ExamClass(exam_id=exam.id, class_id=c.id))
        session.commit()

        exam_id = exam.id
        student_id = student.id

    now = datetime.now(UTC)
    clock = FakeClock(now)

    def worker_start():
        with Session(engine) as worker_session:
            worker_user = worker_session.get(User, student_id)
            return start_student_attempt(worker_session, worker_user, exam_id, clock)

    num_threads = 10
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [executor.submit(worker_start) for _ in range(num_threads)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    # 1. All 10 threads must succeed without error
    assert len(results) == num_threads

    # 2. Every single thread must receive the exact same attempt ID
    unique_ids = {r.id for r in results}
    assert len(unique_ids) == 1, f"Expected 1 unique attempt ID, got: {unique_ids}"

    # 3. Verify in PostgreSQL that exactly 1 row exists in attempts table
    with Session(engine) as verify_session:
        attempts_in_db = verify_session.scalars(
            select(Attempt).where(Attempt.exam_id == exam_id, Attempt.student_id == student_id)
        ).all()
        assert len(attempts_in_db) == 1
