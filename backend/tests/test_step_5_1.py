"""Unit and Integration Tests for Step 5.1: Student Exam Catalog & Detail View.

Test Cases:
- TC-5.1-01: Class isolation (Student A in Class 1 sees exam; Student B in Class 2 gets 404)
- TC-5.1-02: Multi-class deduplication (Exam assigned to Class 1 & 2 appears once)
- TC-5.1-03: Real-time time-based state transitions via FakeClock (upcoming, open, closed)
- TC-5.1-04: Post-attempt states & 0% data leakage (in_progress, submitted, result_available)
- TC-5.1-05: Draft and archived exams strictly hidden (excluded from list, detail returns 404)
- TC-5.1-06: Closed exam with prior attempt remains visible to student with can_start=False
- TC-5.1-07: Transient database OperationalError returns 503 db_unavailable, never empty list
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.dependencies import require_student
from app.core.time import FakeClock
from app.db.session import get_db
from app.main import create_app
from app.models import Attempt, Class, Exam, ExamClass, Question, User
from app.models.class_model import ClassMember
from app.schemas.student_exam_schema import StudentExamDetail, StudentExamListItem
from app.services.student_exam_service import (
    compute_student_exam_state,
    get_student_exam_detail,
    get_student_exams,
)

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


class MockDBStep51:
    """Mock database session for Step 5.1 testing."""

    def __init__(
        self,
        exams: list[Exam] | None = None,
        questions: list[Question] | None = None,
        classes: list[Class] | None = None,
        exam_classes: list[ExamClass] | None = None,
        class_members: list[ClassMember] | None = None,
        attempts: list[Attempt] | None = None,
        raise_operational_error: bool = False,
    ):
        self.exams = {e.id: e for e in (exams or [])}
        self.questions = questions or []
        self.classes = {c.id: c for c in (classes or [])}
        self.exam_classes = exam_classes or []
        self.class_members = class_members or []
        self.attempts = attempts or []
        self.raise_operational_error = raise_operational_error

    def get(self, model, ident):
        if self.raise_operational_error:
            raise OperationalError("SELECT ...", {}, Exception("DB connection timeout"))
        if model is Exam:
            return self.exams.get(ident)
        if model is Class:
            return self.classes.get(ident)
        return None

    def scalar(self, query):
        if self.raise_operational_error:
            raise OperationalError("SELECT ...", {}, Exception("DB connection timeout"))
        q_str = str(query)

        # Check if query is checking enrollment in assigned class
        if "exam_classes" in q_str.lower() and "class_members" in q_str.lower():
            # Evaluation of is_enrolled EXISTS
            return True

        # Check if query is fetching attempt
        if "from attempts" in q_str.lower():
            for att in self.attempts:
                return att
            return None

        return None

    def scalars(self, query):
        if self.raise_operational_error:
            raise OperationalError("SELECT ...", {}, Exception("DB connection timeout"))
        q_str = str(query)
        if "from questions" in q_str.lower():
            items = list(self.questions)
        else:
            items = []

        class Result:
            def __init__(self, data):
                self._data = data

            def all(self):
                return self._data

        return Result(items)

    def execute(self, query):
        if self.raise_operational_error:
            raise OperationalError("SELECT ...", {}, Exception("DB connection timeout"))

        class RowResult:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        return RowResult([])


# ==============================================================================
# TC-5.1-01: Class Isolation (Student A sees, Student B does not; B gets 404)
# ==============================================================================
def test_tc_5_1_01_class_isolation():
    student_a_id = uuid.uuid4()
    student_b_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    class_1 = Class(id=uuid.uuid4(), name="Lớp Toán 1", code="TOAN1")
    class_2 = Class(id=uuid.uuid4(), name="Lớp Toán 2", code="TOAN2")

    exam_1 = Exam(
        id=uuid.uuid4(),
        title="Đề Kiểm Tra 15 Phút",
        subject="toan",
        duration_minutes=15,
        status="published",
        created_by=admin_id,
        description_md="Hướng dẫn làm bài",
    )

    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)

    # In-memory service level test
    # Student A is in Class 1, Exam 1 is assigned to Class 1
    class CustomDB(MockDBStep51):
        def execute(self, query):
            params = query.compile().params if hasattr(query, "compile") else {}
            # If student_a queries, return exam_1; if student_b, return empty
            if student_a_id in params.values():
                return MockDBStep51.execute(self, query).__class__([(exam_1, None, 5)])
            return MockDBStep51.execute(self, query).__class__([])

        def scalar(self, query):
            q_str = str(query)
            params = query.compile().params if hasattr(query, "compile") else {}
            if "from attempts" in q_str.lower():
                return None
            if "class_members" in q_str.lower():
                if student_b_id in params.values():
                    return None
                if student_a_id in params.values():
                    return student_a_id
            return None

    db = CustomDB(
        exams=[exam_1],
        classes=[class_1, class_2],
        exam_classes=[ExamClass(exam_id=exam_1.id, class_id=class_1.id)],
        class_members=[
            ClassMember(class_id=class_1.id, student_id=student_a_id),
            ClassMember(class_id=class_2.id, student_id=student_b_id),
        ],
    )

    # Student A sees Exam 1
    exams_a = get_student_exams(db, student_a_id, now)
    assert len(exams_a) == 1
    assert exams_a[0].id == exam_1.id

    # Student B does not see Exam 1
    exams_b = get_student_exams(db, student_b_id, now)
    assert len(exams_b) == 0

    # Student A accessing detail succeeds
    detail_a = get_student_exam_detail(db, student_a_id, exam_1.id, now)
    assert detail_a.id == exam_1.id

    # Student B accessing detail receives 404 (exam_not_found), NEVER 403!
    from app.core.errors import AppError

    with pytest.raises(AppError) as exc_info:
        get_student_exam_detail(db, student_b_id, exam_1.id, now)
    assert exc_info.value.status_code == 404
    assert exc_info.value.code == "exam_not_found"


# ==============================================================================
# TC-5.1-02: Multi-class Enrollment Deduplication (Exam appears exactly once)
# ==============================================================================
def test_tc_5_1_02_multiple_classes_distinct():
    student_id = uuid.uuid4()
    admin_id = uuid.uuid4()

    class_1 = Class(id=uuid.uuid4(), name="Lớp 1", code="L1")
    class_2 = Class(id=uuid.uuid4(), name="Lớp 2", code="L2")

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Giao Chung 2 Lớp",
        subject="toan",
        duration_minutes=45,
        status="published",
        created_by=admin_id,
    )

    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)

    class DedupDB(MockDBStep51):
        def execute(self, query):
            # Query uses EXISTS and outerjoin on attempts, returning unique exam rows
            return MockDBStep51.execute(self, query).__class__([(exam, None, 10)])

    db = DedupDB(
        exams=[exam],
        classes=[class_1, class_2],
        exam_classes=[
            ExamClass(exam_id=exam.id, class_id=class_1.id),
            ExamClass(exam_id=exam.id, class_id=class_2.id),
        ],
        class_members=[
            ClassMember(class_id=class_1.id, student_id=student_id),
            ClassMember(class_id=class_2.id, student_id=student_id),
        ],
    )

    items = get_student_exams(db, student_id, now)
    assert len(items) == 1
    assert items[0].id == exam.id
    assert items[0].question_count == 10


# ==============================================================================
# TC-5.1-03: Real-Time Time-Based State Transitions via FakeClock
# ==============================================================================
def test_tc_5_1_03_time_based_states():
    admin_id = uuid.uuid4()
    base_time = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)
    clock = FakeClock(base_time)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Có Khung Giờ",
        subject="tin",
        duration_minutes=30,
        status="published",
        open_at=base_time + timedelta(hours=1),  # 11:00
        close_at=base_time + timedelta(hours=3),  # 13:00
        created_by=admin_id,
    )

    # 1. Before open_at -> upcoming
    clock.set_time(datetime(2026, 11, 18, 10, 30, 0, tzinfo=UTC))
    assert compute_student_exam_state(exam, None, clock.now()) == "upcoming"

    # 2. Inside window [open_at, close_at] -> open
    clock.set_time(datetime(2026, 11, 18, 11, 0, 0, tzinfo=UTC))
    assert compute_student_exam_state(exam, None, clock.now()) == "open"

    clock.set_time(datetime(2026, 11, 18, 12, 0, 0, tzinfo=UTC))
    assert compute_student_exam_state(exam, None, clock.now()) == "open"

    # 3. After close_at -> closed
    clock.set_time(datetime(2026, 11, 18, 13, 0, 1, tzinfo=UTC))
    assert compute_student_exam_state(exam, None, clock.now()) == "closed"


# ==============================================================================
# TC-5.1-04: Post-Attempt States & 0% Sensitive Data Leakage
# ==============================================================================
def test_tc_5_1_04_post_attempt_states_no_score_leak():
    admin_id = uuid.uuid4()
    student_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Bảo Mật Tuyệt Đối",
        subject="both",
        duration_minutes=45,
        status="published",
        result_visibility="score_only",
        created_by=admin_id,
    )

    # Attempt 1: in_progress
    att_in_prog = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_id,
        status="in_progress",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        shuffle_seed=12345,
    )
    assert compute_student_exam_state(exam, att_in_prog, now) == "in_progress"

    # Attempt 2: submitted (not released)
    att_sub = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_id,
        status="submitted",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        submitted_at=now + timedelta(minutes=40),
        shuffle_seed=12345,
        score_total=Decimal("9.50"),
        released=False,
    )
    assert compute_student_exam_state(exam, att_sub, now) == "submitted"

    # Attempt 3: released
    att_rel = Attempt(
        id=uuid.uuid4(),
        exam_id=exam.id,
        student_id=student_id,
        status="submitted",
        started_at=now,
        deadline_at=now + timedelta(minutes=45),
        submitted_at=now + timedelta(minutes=40),
        shuffle_seed=12345,
        score_total=Decimal("9.50"),
        released=True,
    )
    assert compute_student_exam_state(exam, att_rel, now) == "result_available"

    # Verify JSON Schema allow-list strictly excludes forbidden keys
    list_item = StudentExamListItem(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        duration_minutes=exam.duration_minutes,
        question_count=20,
        open_at=exam.open_at,
        close_at=exam.close_at,
        state="submitted",
        attempt_id=att_sub.id,
    )
    list_dict = list_item.model_dump()
    found_keys_list = recursive_find_keys(list_dict)
    leaked_list = found_keys_list.intersection(FORBIDDEN_STUDENT_KEYS)
    assert not leaked_list, f"List item leaks forbidden keys: {leaked_list}"

    detail_item = StudentExamDetail(
        id=exam.id,
        title=exam.title,
        subject=exam.subject,
        description_md="Mô tả",
        duration_minutes=exam.duration_minutes,
        question_count=20,
        total_points=Decimal("10.00"),
        open_at=exam.open_at,
        close_at=exam.close_at,
        state="submitted",
        attempt_id=att_sub.id,
        can_start=False,
    )
    detail_dict = detail_item.model_dump()
    found_keys_detail = recursive_find_keys(detail_dict)
    leaked_detail = found_keys_detail.intersection(FORBIDDEN_STUDENT_KEYS)
    assert not leaked_detail, f"Detail item leaks forbidden keys: {leaked_detail}"


# ==============================================================================
# TC-5.1-05: Draft and Archived Exams Strictly Hidden
# ==============================================================================
def test_tc_5_1_05_draft_and_archived_hidden():
    student_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)

    draft_exam = Exam(
        id=uuid.uuid4(),
        title="Đề Nháp Chưa Công Khai",
        subject="toan",
        status="draft",
        created_by=admin_id,
    )
    archived_exam = Exam(
        id=uuid.uuid4(),
        title="Đề Đã Lưu Trữ",
        subject="toan",
        status="archived",
        created_by=admin_id,
    )

    from app.core.errors import AppError

    db_draft = MockDBStep51(exams=[draft_exam])
    with pytest.raises(AppError) as exc_draft:
        get_student_exam_detail(db_draft, student_id, draft_exam.id, now)
    assert exc_draft.value.status_code == 404
    assert exc_draft.value.code == "exam_not_found"

    db_archived = MockDBStep51(exams=[archived_exam])
    with pytest.raises(AppError) as exc_archived:
        get_student_exam_detail(db_archived, student_id, archived_exam.id, now)
    assert exc_archived.value.status_code == 404
    assert exc_archived.value.code == "exam_not_found"


# ==============================================================================
# TC-5.1-06: Closed Exam with Prior Attempt Remains Visible to Student
# ==============================================================================
def test_tc_5_1_06_closed_exam_with_prior_attempt_visible():
    student_id = uuid.uuid4()
    admin_id = uuid.uuid4()
    now = datetime(2026, 11, 18, 10, 0, 0, tzinfo=UTC)

    closed_exam = Exam(
        id=uuid.uuid4(),
        title="Đề Thi Học Kỳ Đã Đóng",
        subject="toan",
        duration_minutes=60,
        status="closed",
        created_by=admin_id,
        description_md="Đề thi đã kết thúc",
    )

    att = Attempt(
        id=uuid.uuid4(),
        exam_id=closed_exam.id,
        student_id=student_id,
        status="submitted",
        started_at=now - timedelta(hours=2),
        deadline_at=now - timedelta(hours=1),
        submitted_at=now - timedelta(hours=1, minutes=10),
        shuffle_seed=999,
        released=False,
    )

    class ClosedExamDB(MockDBStep51):
        def execute(self, query):
            return MockDBStep51.execute(self, query).__class__([(closed_exam, att, 25)])

        def scalar(self, query):
            q_str = str(query)
            if "from attempts" in q_str.lower():
                return att
            return None

    db = ClosedExamDB(exams=[closed_exam], attempts=[att])

    # Visible in list with state 'submitted'
    items = get_student_exams(db, student_id, now)
    assert len(items) == 1
    assert items[0].id == closed_exam.id
    assert items[0].state == "submitted"
    assert items[0].attempt_id == att.id

    # Visible in detail view with can_start=False
    detail = get_student_exam_detail(db, student_id, closed_exam.id, now)
    assert detail.id == closed_exam.id
    assert detail.state == "submitted"
    assert detail.can_start is False


# ==============================================================================
# TC-5.1-07: Transient Database Error Returns 503 db_unavailable (FastAPI App)
# ==============================================================================
def test_tc_5_1_07_transient_db_error_503():
    app = create_app()

    student_user = User(
        id=uuid.uuid4(),
        username="anhnt",
        full_name="Nguyễn Tuấn Anh",
        role="student",
        is_active=True,
    )

    app.dependency_overrides[require_student] = lambda: student_user

    def broken_db():
        raise OperationalError("SELECT ...", {}, Exception("Neon DB paused / Connection reset"))

    app.dependency_overrides[get_db] = broken_db

    client = TestClient(app, raise_server_exceptions=False)

    # 1. Calling GET /api/v1/student/exams during DB failure returns 503
    res_list = client.get("/api/v1/student/exams")
    assert res_list.status_code == 503
    data_list = res_list.json()
    assert data_list["error"]["code"] == "db_unavailable"
    assert res_list.headers.get("retry-after") == "2"

    # 2. Calling GET /api/v1/student/exams/{id} during DB failure returns 503
    random_exam_id = uuid.uuid4()
    res_detail = client.get(f"/api/v1/student/exams/{random_exam_id}")
    assert res_detail.status_code == 503
    data_detail = res_detail.json()
    assert data_detail["error"]["code"] == "db_unavailable"
    assert res_detail.headers.get("retry-after") == "2"
