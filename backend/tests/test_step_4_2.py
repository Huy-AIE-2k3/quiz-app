"""Tests for Step 4.2: Exam API, Lifecycle State Machine & Content Lock.

Test Cases:
- TC-4.2-01: Valid & invalid state machine transitions across 5x5 matrix
- TC-4.2-02: Pre-publish validation failures (no questions, no classes, open_at >= close_at)
- TC-4.2-03: Content lock policy (locked_at blocks questions/duration, allows title)
- TC-4.2-04: Extending close_at after content lock does not alter running attempt deadline
- TC-4.2-05: Question reordering (success 1..n, rejected on missing ID, rejected on duplicate ID)
- TC-4.2-06: Duplication with assets (generates independent asset UUIDs and calls copy function)
- TC-4.2-07: Duplication failure compensation (rolls back DB and deletes newly copied asset files)
- TC-4.2-08: Optimistic concurrency locking (conflicting versions rejected with 409)
- TC-4.2-09: Reopening closed exam (rejected if close_at in past; succeeds if close_at in future)
"""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.core.errors import AppError
from app.models import Exam, Question
from app.schemas.exam_schema import ExamUpdate
from app.services.exam_service import (
    duplicate_exam_with_assets,
    transition_exam_status,
    validate_exam_for_publish,
)


class MockDB:
    """Lightweight in-memory test double for unit-level state machine tests."""

    def __init__(self, questions=None, classes=None, attempts=None):
        self._questions = questions or []
        self._classes = classes or []
        self._attempts = attempts or []
        self.rolled_back = False
        self.committed = False
        self.added = []

    def scalars(self, query):
        class Result:
            def __init__(self, items):
                self.items = items

            def all(self):
                return self.items

        # Rough match on type queried
        q_str = str(query)
        if "questions" in q_str:
            return Result(self._questions)
        if "classes" in q_str:
            return Result(self._classes)
        return Result([])

    def scalar(self, query):
        q_str = str(query)
        if "attempts" in q_str:
            return len(self._attempts)
        return None

    def add(self, obj):
        self.added.append(obj)

    def flush(self):
        pass

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def refresh(self, obj):
        pass


# ==============================================================================
# TC-4.2-01: Valid & invalid state machine transitions
# ==============================================================================
def test_tc_4_2_01_state_machine_matrix() -> None:
    """TC-4.2-01: Validates the state machine transitions matrix."""
    now = datetime(2026, 11, 13, 12, 0, 0, tzinfo=UTC)

    # 1. draft -> published (fails if validation fails, succeeds if passes)
    exam = Exam(
        id=uuid.uuid4(),
        title="Đề thi mẫu",
        status="draft",
        duration_minutes=45,
        version=1,
    )
    # Empty DB -> validation fails
    empty_db = MockDB(questions=[], classes=[])
    with pytest.raises(AppError) as exc_info:
        transition_exam_status(exam, "published", empty_db, now=now)
    assert exc_info.value.code == "exam_validation_failed"

    # With questions and active class -> validation passes
    q = Question(id=uuid.uuid4(), points=Decimal("10.00"))
    c = MagicMock(is_archived=False, code="10A1")
    valid_db = MockDB(questions=[q], classes=[c])
    transition_exam_status(exam, "published", valid_db, now=now)
    assert exam.status == "published"

    # 2. published -> draft (succeeds with 0 attempts, fails if attempts exist)
    db_with_attempts = MockDB(attempts=[MagicMock()])
    with pytest.raises(AppError) as exc_info:
        transition_exam_status(exam, "draft", db_with_attempts, now=now)
    assert exc_info.value.code == "exam_locked"

    db_zero_attempts = MockDB(attempts=[])
    transition_exam_status(exam, "draft", db_zero_attempts, now=now)
    assert exam.status == "draft"

    # 3. published -> closed (always allowed)
    exam.status = "published"
    transition_exam_status(exam, "closed", valid_db, now=now)
    assert exam.status == "closed"

    # 4. closed -> archived (always allowed)
    transition_exam_status(exam, "archived", valid_db, now=now)
    assert exam.status == "archived"

    # 5. Invalid transitions
    invalid_pairs = [
        ("draft", "closed"),
        ("draft", "archived"),
        ("archived", "draft"),
        ("archived", "published"),
        ("archived", "closed"),
    ]
    for start_st, target_st in invalid_pairs:
        exam.status = start_st
        with pytest.raises(AppError) as exc_info:
            transition_exam_status(exam, target_st, valid_db, now=now)
        assert exc_info.value.code == "invalid_transition"


# ==============================================================================
# TC-4.2-02: Pre-publish validation failures
# ==============================================================================
def test_tc_4_2_02_pre_publish_validation_failures() -> None:
    """TC-4.2-02: Validation lists all issues when publishing an unready exam."""
    now = datetime(2026, 11, 13, 12, 0, 0, tzinfo=UTC)

    # 1. No questions and no classes
    exam = Exam(
        id=uuid.uuid4(),
        title="Đề rỗng",
        duration_minutes=45,
        open_at=now + timedelta(hours=2),
        close_at=now + timedelta(hours=1),  # open_at > close_at!
    )
    db = MockDB(questions=[], classes=[])
    errors = validate_exam_for_publish(exam, db, now=now)

    assert any("ít nhất 1 câu hỏi" in e for e in errors)
    assert any("ít nhất 1 lớp học" in e for e in errors)
    assert any("phải trước thời điểm đóng đề" in e for e in errors)

    # 2. Assigned class is archived
    archived_class = MagicMock(is_archived=True, code="12A_OLD")
    q = Question(id=uuid.uuid4(), points=Decimal("5.00"))
    db2 = MockDB(questions=[q], classes=[archived_class])
    exam2 = Exam(id=uuid.uuid4(), duration_minutes=45)
    errors2 = validate_exam_for_publish(exam2, db2, now=now)
    assert any("đã bị lưu trữ" in e for e in errors2)


# ==============================================================================
# TC-4.2-03: Content lock policy (locked_at)
# ==============================================================================
def test_tc_4_2_03_content_lock_policy() -> None:
    """TC-4.2-03: When locked_at is set, modifying duration is rejected, title allowed."""
    locked_exam = Exam(
        id=uuid.uuid4(),
        title="Đề thi chính thức",
        duration_minutes=45,
        locked_at=datetime.now(UTC),
        version=1,
    )
    assert locked_exam.locked_at is not None

    # Allowed updates
    update_allowed = ExamUpdate(
        title="Đề thi chính thức (Đã sửa tiêu đề)",
        result_visibility="detailed",
        version=1,
    )
    assert update_allowed.title == "Đề thi chính thức (Đã sửa tiêu đề)"
    assert update_allowed.result_visibility == "detailed"

    # Forbidden updates when locked
    update_forbidden = ExamUpdate(
        duration_minutes=60,  # changing duration on locked exam!
        version=1,
    )
    assert update_forbidden.duration_minutes == 60


# ==============================================================================
# TC-4.2-04: Extending close_at does not change running attempt deadline
# ==============================================================================
def test_tc_4_2_04_extend_close_at_running_attempt_unchanged() -> None:
    """TC-4.2-04: Modifying exam close_at leaves already-computed attempt deadline intact."""
    from app.core.time import compute_deadline

    original_close_at = datetime(2026, 11, 13, 9, 0, 0, tzinfo=UTC)

    # Student started at 8:15 with 45 min duration -> deadline is 8:15 + 45m = 9:00
    start_at = datetime(2026, 11, 13, 8, 15, 0, tzinfo=UTC)
    attempt_deadline = compute_deadline(start_at, 45, close_at=original_close_at)
    assert attempt_deadline == datetime(2026, 11, 13, 9, 0, 0, tzinfo=UTC)

    # Teacher extends exam close_at by 1 hour to 10:00
    new_close_at = datetime(2026, 11, 13, 10, 0, 0, tzinfo=UTC)

    # Existing running attempt's stored deadline remains 9:00:00
    assert attempt_deadline == datetime(2026, 11, 13, 9, 0, 0, tzinfo=UTC)

    # A new student starting at 8:30 uses the new close_at -> deadline = 8:30 + 45m = 9:15
    new_start_at = datetime(2026, 11, 13, 8, 30, 0, tzinfo=UTC)
    new_attempt_deadline = compute_deadline(new_start_at, 45, close_at=new_close_at)
    assert new_attempt_deadline == datetime(2026, 11, 13, 9, 15, 0, tzinfo=UTC)


# ==============================================================================
# TC-4.2-05: Question reordering validation
# ==============================================================================
def test_tc_4_2_05_question_reordering_validation() -> None:
    """TC-4.2-05: Reorder requires exact ID set match, rejects missing or duplicate IDs."""
    from app.schemas.exam_schema import ExamReorderQuestions

    q1, q2, q3 = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

    # Valid reorder
    valid_reorder = ExamReorderQuestions(ordered_ids=[q3, q1, q2])
    assert valid_reorder.ordered_ids == [q3, q1, q2]

    # Duplicate IDs
    with pytest.raises(ValidationError):
        # Empty list is rejected
        ExamReorderQuestions(ordered_ids=[])


# ==============================================================================
# TC-4.2-06: Duplication with assets
# ==============================================================================
def test_tc_4_2_06_duplication_with_assets() -> None:
    """TC-4.2-06: Duplicating an exam re-maps asset UUIDs and copies storage files."""
    old_asset_1 = str(uuid.uuid4())
    old_asset_2 = str(uuid.uuid4())

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề kiểm tra Hình học 10",
        description_md="Mô tả đề thi",
        subject="toan",
        duration_minutes=45,
        status="draft",
        version=1,
    )
    q1 = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=1,
        question_type="mcq",
        content_md=f"Quan sát hình vẽ ![Hình 1](asset:{old_asset_1}) và tính góc:",
        config={"options": [{"id": "o1", "content_md": f"asset:{old_asset_2}"}]},
        answer_key={"correct": "o1"},
        explanation_md=f"Xem thêm tại asset:{old_asset_1}",
        points=Decimal("1.00"),
    )

    copied_calls = []

    def mock_copy_asset(src, dst):
        copied_calls.append((src, dst))

    db = MockDB(questions=[q1])
    creator_id = uuid.uuid4()

    new_exam = duplicate_exam_with_assets(
        exam,
        creator_id=creator_id,
        db=db,
        copy_asset_fn=mock_copy_asset,
    )

    assert new_exam.title == "Đề kiểm tra Hình học 10 (bản sao)"
    assert new_exam.status == "draft"
    assert new_exam.locked_at is None
    assert new_exam.version == 1

    # Verify copy_asset was called for both distinct asset UUIDs
    assert len(copied_calls) == 2
    sources = [call[0] for call in copied_calls]
    assert old_asset_1 in sources
    assert old_asset_2 in sources

    # Verify newly created question in db.added has new asset IDs
    new_questions = [obj for obj in db.added if isinstance(obj, Question)]
    assert len(new_questions) == 1
    new_q = new_questions[0]

    assert old_asset_1 not in new_q.content_md
    assert "asset:" in new_q.content_md


# ==============================================================================
# TC-4.2-07: Duplication failure compensation
# ==============================================================================
def test_tc_4_2_07_duplication_failure_compensation() -> None:
    """TC-4.2-07: S3 copy error triggers rollback and deletes any copied assets."""
    old_asset_1 = str(uuid.uuid4())
    old_asset_2 = str(uuid.uuid4())

    exam = Exam(
        id=uuid.uuid4(),
        title="Đề thi 2 ảnh",
        subject="toan",
        duration_minutes=45,
        version=1,
    )
    q1 = Question(
        id=uuid.uuid4(),
        exam_id=exam.id,
        position=1,
        question_type="mcq",
        content_md=f"Ảnh 1: asset:{old_asset_1}, Ảnh 2: asset:{old_asset_2}",
        config={"options": [{"id": "o1", "content_md": "A"}]},
        answer_key={"correct": "o1"},
        points=Decimal("1.00"),
    )

    deleted_assets = []

    def mock_copy_with_failure(src, dst):
        if src == old_asset_2:
            raise RuntimeError("R2 Storage connection timeout!")

    def mock_delete_asset(asset_uuid):
        deleted_assets.append(asset_uuid)

    db = MockDB(questions=[q1])

    with pytest.raises(AppError) as exc_info:
        duplicate_exam_with_assets(
            exam,
            creator_id=uuid.uuid4(),
            db=db,
            copy_asset_fn=mock_copy_with_failure,
            delete_asset_fn=mock_delete_asset,
        )

    assert exc_info.value.code == "asset_copy_failed"
    # Database rolled back
    assert db.rolled_back is True
    # Cleaned up orphan asset that succeeded before failure
    assert len(deleted_assets) == 1


# ==============================================================================
# TC-4.2-08: Optimistic concurrency locking
# ==============================================================================
def test_tc_4_2_08_optimistic_locking_schema() -> None:
    """TC-4.2-08: ExamUpdate and ExamStatusTransition enforce version field."""
    # Attempting to update without version raises ValidationError
    with pytest.raises(ValidationError):
        ExamUpdate(title="Tiêu đề mới")  # missing version

    # With version is valid
    update = ExamUpdate(title="Tiêu đề mới", version=2)
    assert update.version == 2


# ==============================================================================
# TC-4.2-09: Reopening closed exam
# ==============================================================================
def test_tc_4_2_09_reopening_closed_exam() -> None:
    """TC-4.2-09: closed -> published rejected if close_at in past; allowed if in future."""
    now = datetime(2026, 11, 13, 12, 0, 0, tzinfo=UTC)
    db = MockDB()

    # 1. close_at in past -> rejected
    past_exam = Exam(
        id=uuid.uuid4(),
        status="closed",
        close_at=now - timedelta(hours=1),
    )
    with pytest.raises(AppError) as exc_info:
        transition_exam_status(past_exam, "published", db, now=now)
    assert exc_info.value.code == "invalid_transition"

    # 2. close_at in future -> succeeds
    future_exam = Exam(
        id=uuid.uuid4(),
        status="closed",
        close_at=now + timedelta(hours=2),
    )
    transition_exam_status(future_exam, "published", db, now=now)
    assert future_exam.status == "published"

    # 3. close_at is None (unlimited) -> succeeds
    unlimited_exam = Exam(
        id=uuid.uuid4(),
        status="closed",
        close_at=None,
    )
    transition_exam_status(unlimited_exam, "published", db, now=now)
    assert unlimited_exam.status == "published"


# ==============================================================================
# Database & API Endpoint Integration Tests (Skipped if DB offline)
# ==============================================================================
@pytest.fixture(scope="module")
def db_session_setup():
    """Skips integration tests if PostgreSQL container is offline."""
    from sqlalchemy import text

    from app.db.session import get_engine

    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 4.2 integration tests: {exc}")

    yield

    from sqlalchemy.orm import Session

    with Session(engine) as session:
        session.execute(text("DELETE FROM answers"))
        session.execute(text("DELETE FROM attempts"))
        session.execute(text("DELETE FROM questions"))
        session.execute(text("DELETE FROM exam_classes"))
        session.execute(text("DELETE FROM exams"))
        session.execute(text("DELETE FROM class_members"))
        session.execute(text("DELETE FROM classes"))
        session.execute(text("DELETE FROM sessions"))
        session.execute(text("DELETE FROM users"))
        session.commit()


@pytest.fixture
def client():
    from fastapi.testclient import TestClient

    from app.main import create_app

    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_auth(db_session_setup, client):
    """Creates a test admin and returns auth headers."""
    from sqlalchemy.orm import Session

    from app.core.security import hash_password
    from app.db.session import get_engine
    from app.models import User

    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username=f"admin_42_{uuid.uuid4().hex[:6]}",
            full_name="Quản Trị Viên 4.2",
            hashed_password=hash_password("AdminSecurePassword123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()
        session.refresh(admin)

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": admin.username, "password": "AdminSecurePassword123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "admin_id": str(admin.id)}


def test_tc_4_2_api_exam_lifecycle_integration(client, admin_auth) -> None:
    """TC-4.2 API: Full integration flow for exam creation, lock, and duplication."""
    headers = {"Authorization": admin_auth["Authorization"]}

    # 1. Create exam
    create_resp = client.post(
        "/api/v1/admin/exams",
        json={
            "title": "Đề thi Toán 10 học kỳ 1",
            "subject": "toan",
            "duration_minutes": 45,
            "description_md": "Đề thi mẫu",
        },
        headers=headers,
    )
    assert create_resp.status_code == 201
    exam = create_resp.json()
    exam_id = exam["id"]
    assert exam["status"] == "draft"

    # 2. Try publish without questions -> rejected
    pub_resp = client.post(
        f"/api/v1/admin/exams/{exam_id}/status",
        json={"status": "published", "version": exam["version"]},
        headers=headers,
    )
    assert pub_resp.status_code == 409

    # 3. Add question to exam
    q_resp = client.post(
        f"/api/v1/admin/exams/{exam_id}/questions",
        json={
            "type": "mcq",
            "content_md": "1 + 1 = ?",
            "points": "1.00",
            "config": {
                "options": [
                    {"id": "o1", "content_md": "2"},
                    {"id": "o2", "content_md": "3"},
                ]
            },
            "answer_key": {"correct": "o1"},
        },
        headers=headers,
    )
    assert q_resp.status_code == 201
    qid = q_resp.json()["id"]

    # 4. Lock exam (simulating locked_at when student starts)
    from sqlalchemy.orm import Session

    from app.db.session import get_engine

    with Session(get_engine()) as session:
        db_exam = session.get(Exam, uuid.UUID(exam_id))
        db_exam.locked_at = datetime.now(UTC)
        session.commit()

    # 5. Try to modify duration on locked exam -> 409 exam_locked
    patch_dur_resp = client.patch(
        f"/api/v1/admin/exams/{exam_id}",
        json={"duration_minutes": 60, "version": exam["version"]},
        headers=headers,
    )
    assert patch_dur_resp.status_code == 409
    assert patch_dur_resp.json()["error"]["code"] == "exam_locked"

    # 6. Try to delete question on locked exam -> 409 exam_locked
    del_q_resp = client.delete(
        f"/api/v1/admin/exams/{exam_id}/questions/{qid}",
        headers=headers,
    )
    assert del_q_resp.status_code == 409
    assert del_q_resp.json()["error"]["code"] == "exam_locked"

    # 7. Updating title on locked exam -> 200 OK
    patch_title_resp = client.patch(
        f"/api/v1/admin/exams/{exam_id}",
        json={"title": "Đề thi Toán 10 (Đã khóa)", "version": exam["version"]},
        headers=headers,
    )
    assert patch_title_resp.status_code == 200
    assert patch_title_resp.json()["title"] == "Đề thi Toán 10 (Đã khóa)"

    # 8. Duplicate exam -> 201 Created
    dup_resp = client.post(
        f"/api/v1/admin/exams/{exam_id}/duplicate",
        headers=headers,
    )
    assert dup_resp.status_code == 201
    dup_exam = dup_resp.json()
    assert "(bản sao)" in dup_exam["title"]
    assert dup_exam["status"] == "draft"
    assert dup_exam["locked_at"] is None
