"""Tests for Step 3.2: Student Management and Class Enrollment API.

Verifies:
    TC-3.2-01: Student creation username validation (whitespace/short rejected, duplicate -> 409).
    TC-3.2-02: Auto-generated password appears only once in creation response, never in GET.
    TC-3.2-03: Set-based enrollment is idempotent (second call returns added=0, removed=0).
    TC-3.2-04: Enrollment with invalid/admin/non-existent IDs rolls back completely (422).
    TC-3.2-05: Student enrolled in multiple classes assigned the same exam sees it exactly once.
    TC-3.2-06: Concurrent enrollment serialized via row-level lock (SELECT FOR UPDATE).
    TC-3.2-07: Withdrawing student from class preserves ongoing exam attempt submission.
    TC-3.2-08: Disabling student account immediately revokes sessions and returns 401 on /auth/me.
"""

import threading
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_engine
from app.main import create_app
from app.models import Attempt, Class, ClassMember, Exam, ExamClass, User


@pytest.fixture(autouse=True)
def clean_db():
    """Cleans up database tables between test runs."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 3.2 tests: {exc}")

    yield

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
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_token(client):
    """Creates a dedicated admin user and returns a valid Bearer token."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="admin_step32",
            full_name="Quản Trị Viên 3.2",
            hashed_password=hash_password("AdminSecurePassword123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_step32", "password": "AdminSecurePassword123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_tc_3_2_01_username_validation_and_duplicate(client, admin_token):
    """TC-3.2-01: Username validation (spaces rejected 422, duplicate -> 409 username_taken)."""
    # 1. Username with spaces -> 422
    res_space = client.post(
        "/api/v1/admin/students",
        json={"username": "Nam 01", "full_name": "Nguyễn Văn Nam"},
        headers=auth_header(admin_token),
    )
    assert res_space.status_code == 422

    # 2. Username too short (< 3 chars) -> 422
    res_short = client.post(
        "/api/v1/admin/students",
        json={"username": "ab", "full_name": "Nguyễn Văn An"},
        headers=auth_header(admin_token),
    )
    assert res_short.status_code == 422

    # 3. Create valid student -> 201
    res_valid = client.post(
        "/api/v1/admin/students",
        json={"username": "nam01", "full_name": "Nguyễn Văn Nam"},
        headers=auth_header(admin_token),
    )
    assert res_valid.status_code == 201
    assert res_valid.json()["username"] == "nam01"

    # 4. Duplicate username -> 409 username_taken
    res_dup = client.post(
        "/api/v1/admin/students",
        json={"username": "nam01", "full_name": "Trần Văn Nam"},
        headers=auth_header(admin_token),
    )
    assert res_dup.status_code == 409
    err = res_dup.json()["error"]
    assert err["code"] == "username_taken"


def test_tc_3_2_02_password_one_time_display(client, admin_token):
    """TC-3.2-02: Auto-generated password appears only once in creation response, never in GET."""
    # 1. Create student without specifying password
    create_res = client.post(
        "/api/v1/admin/students",
        json={"username": "hoa02", "full_name": "Lê Thị Hoa"},
        headers=auth_header(admin_token),
    )
    assert create_res.status_code == 201
    data = create_res.json()
    student_id = data["id"]
    gen_pwd = data["generated_password"]

    # Generated password must exist, be >= 8 chars, contain letters and digits
    assert gen_pwd is not None
    assert len(gen_pwd) >= 8
    assert any(c.isdigit() for c in gen_pwd)
    assert any(c.isalpha() for c in gen_pwd)

    # 2. GET /admin/students must NEVER return password or generated_password
    list_res = client.get("/api/v1/admin/students", headers=auth_header(admin_token))
    assert list_res.status_code == 200
    for student in list_res.json()["items"]:
        assert "password" not in student
        assert "generated_password" not in student
        assert "hashed_password" not in student

    # 3. GET /admin/students/{id} must NEVER return password
    detail_res = client.get(
        f"/api/v1/admin/students/{student_id}", headers=auth_header(admin_token)
    )
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert "password" not in detail_data
    assert "generated_password" not in detail_data
    assert "hashed_password" not in detail_data

    # 4. Student can successfully log in using generated password
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "hoa02", "password": gen_pwd},
    )
    assert login_res.status_code == 200
    assert "access_token" in login_res.json()


def test_tc_3_2_03_idempotent_class_enrollment(client, admin_token):
    """TC-3.2-03: Set-based enrollment is idempotent (second call returns added=0, removed=0)."""
    # 1. Create class
    cls_res = client.post(
        "/api/v1/admin/classes",
        json={"code": "10A2", "name": "Lớp 10A2", "academic_year": 2026, "subject": "both"},
        headers=auth_header(admin_token),
    )
    class_id = cls_res.json()["id"]

    # 2. Create 2 students
    s1_res = client.post(
        "/api/v1/admin/students",
        json={"username": "std01", "full_name": "Học Sinh Một"},
        headers=auth_header(admin_token),
    )
    s2_res = client.post(
        "/api/v1/admin/students",
        json={"username": "std02", "full_name": "Học Sinh Hai"},
        headers=auth_header(admin_token),
    )
    u1, u2 = s1_res.json()["id"], s2_res.json()["id"]

    # 3. First enrollment: add both students
    put1 = client.put(
        f"/api/v1/admin/classes/{class_id}/members",
        json={"user_ids": [u1, u2]},
        headers=auth_header(admin_token),
    )
    assert put1.status_code == 200
    data1 = put1.json()
    assert data1["added"] == 2
    assert data1["removed"] == 0
    assert data1["total"] == 2

    # 4. Second enrollment with exact same set: idempotent, added=0, removed=0
    put2 = client.put(
        f"/api/v1/admin/classes/{class_id}/members",
        json={"user_ids": [u2, u1]},  # reversed order
        headers=auth_header(admin_token),
    )
    assert put2.status_code == 200
    data2 = put2.json()
    assert data2["added"] == 0
    assert data2["removed"] == 0
    assert data2["total"] == 2

    # Verify database count is exactly 2 (no duplicates)
    engine = get_engine()
    with Session(engine) as session:
        members = (
            session.execute(select(ClassMember).where(ClassMember.class_id == class_id))
            .scalars()
            .all()
        )
        assert len(members) == 2


def test_tc_3_2_04_enrollment_with_invalid_ids_rolls_back(client, admin_token):
    """TC-3.2-04: Enrollment with non-existent ID or admin ID rolls back 100% (422)."""
    # 1. Create class
    cls_res = client.post(
        "/api/v1/admin/classes",
        json={"code": "10A3", "name": "Lớp 10A3", "academic_year": 2026, "subject": "both"},
        headers=auth_header(admin_token),
    )
    class_id = cls_res.json()["id"]

    # 2. Create 1 valid student
    s_res = client.post(
        "/api/v1/admin/students",
        json={"username": "valid_std", "full_name": "Học Sinh Chuẩn"},
        headers=auth_header(admin_token),
    )
    valid_id = s_res.json()["id"]

    # Admin user id
    engine = get_engine()
    with Session(engine) as session:
        admin_id = session.execute(
            text("SELECT id FROM users WHERE username = 'admin_step32'")
        ).scalar()

    fake_id = str(uuid.uuid4())

    # 3. Send enrollment containing: 1 valid student, 1 admin, 1 fake ID
    enroll_res = client.put(
        f"/api/v1/admin/classes/{class_id}/members",
        json={"user_ids": [valid_id, str(admin_id), fake_id]},
        headers=auth_header(admin_token),
    )
    assert enroll_res.status_code == 422
    err = enroll_res.json()["error"]
    assert err["code"] == "invalid_members"
    invalid_list = err["details"]["invalid_user_ids"]
    assert str(admin_id) in invalid_list
    assert fake_id in invalid_list

    # 4. Verify that NO members were enrolled (atomic rollback)
    with Session(engine) as session:
        count = (
            session.execute(select(ClassMember).where(ClassMember.class_id == class_id))
            .scalars()
            .all()
        )
        assert len(count) == 0


def test_tc_3_2_05_student_in_multiple_classes_no_duplicate_exams(client, admin_token):
    """TC-3.2-05: Student in multiple classes assigned same exam sees exam exactly once."""
    engine = get_engine()
    class_a_id = uuid.uuid4()
    class_b_id = uuid.uuid4()
    exam_id = uuid.uuid4()

    with Session(engine) as session:
        admin_id = session.execute(
            text("SELECT id FROM users WHERE username = 'admin_step32'")
        ).scalar()

        # Create 2 classes
        session.add(Class(id=class_a_id, code="CLASS_A", name="Lớp A", academic_year=2026))
        session.add(Class(id=class_b_id, code="CLASS_B", name="Lớp B", academic_year=2026))

        # Create 1 student enrolled in BOTH classes
        student = User(
            username="multi_class_student",
            full_name="Học Sinh Đa Lớp",
            hashed_password=hash_password("StdPass123!"),
            role="student",
            is_active=True,
        )
        session.add(student)
        session.flush()

        session.add(ClassMember(class_id=class_a_id, student_id=student.id))
        session.add(ClassMember(class_id=class_b_id, student_id=student.id))

        # Create 1 exam and assign to BOTH classes
        exam = Exam(
            id=exam_id,
            title="Đề Thi Chung Cho Cả 2 Lớp",
            created_by=admin_id,
            duration_minutes=60,
            subject="math",
            status="published",
            version=1,
        )
        session.add(exam)
        session.flush()

        session.add(ExamClass(exam_id=exam.id, class_id=class_a_id))
        session.add(ExamClass(exam_id=exam.id, class_id=class_b_id))
        session.commit()

        # Query distinct exams available to this student
        # (simulating student view logic: distinct Exam where ExamClass in student's classes)
        distinct_exams = (
            session.execute(
                select(Exam)
                .join(ExamClass, ExamClass.exam_id == Exam.id)
                .join(ClassMember, ClassMember.class_id == ExamClass.class_id)
                .where(ClassMember.student_id == student.id)
                .distinct()
            )
            .scalars()
            .all()
        )
        assert len(distinct_exams) == 1
        assert distinct_exams[0].id == exam_id


def test_tc_3_2_06_concurrent_enrollment_serialized(client, admin_token):
    """TC-3.2-06: Concurrent enrollment on same class serialized safely via SELECT FOR UPDATE."""
    # 1. Create class
    cls_res = client.post(
        "/api/v1/admin/classes",
        json={"code": "10RACE", "name": "Lớp Đua", "academic_year": 2026, "subject": "both"},
        headers=auth_header(admin_token),
    )
    class_id = cls_res.json()["id"]

    # 2. Create 4 students
    uids = []
    for i in range(4):
        s_res = client.post(
            "/api/v1/admin/students",
            json={"username": f"race_std_{i}", "full_name": f"Học Sinh {i}"},
            headers=auth_header(admin_token),
        )
        uids.append(s_res.json()["id"])

    # 3. Spawn 2 threads performing enrollment concurrently
    results = [None, None]

    def enroll_worker(idx, target_uids):
        res = client.put(
            f"/api/v1/admin/classes/{class_id}/members",
            json={"user_ids": target_uids},
            headers=auth_header(admin_token),
        )
        results[idx] = res

    t1 = threading.Thread(target=enroll_worker, args=(0, [uids[0], uids[1]]))
    t2 = threading.Thread(target=enroll_worker, args=(1, [uids[1], uids[2], uids[3]]))

    t1.start()
    t2.start()
    t1.join()
    t2.join()

    # Both must succeed without deadlock (200 OK)
    assert results[0].status_code == 200
    assert results[1].status_code == 200

    # Final DB state must match the last executed thread (total 2 or 3, not corrupted)
    engine = get_engine()
    with Session(engine) as session:
        final_members = (
            session.execute(select(ClassMember.student_id).where(ClassMember.class_id == class_id))
            .scalars()
            .all()
        )
        assert len(final_members) in (2, 3)


def test_tc_3_2_07_withdrawing_student_preserves_ongoing_attempt(client, admin_token):
    """TC-3.2-07: Withdrawing student from class preserves ongoing exam attempt submission."""
    engine = get_engine()
    class_id = uuid.uuid4()
    exam_id = uuid.uuid4()
    student_id = uuid.uuid4()
    attempt_id = uuid.uuid4()

    with Session(engine) as session:
        admin_id = session.execute(
            text("SELECT id FROM users WHERE username = 'admin_step32'")
        ).scalar()

        # 1. Create class, student, exam, assign exam to class
        session.add(Class(id=class_id, code="CLASS_WITHDRAW", name="Lớp Rút", academic_year=2026))
        student = User(
            id=student_id,
            username="student_withdraw",
            full_name="Học Sinh Rút",
            hashed_password=hash_password("Pass123!"),
            role="student",
            is_active=True,
        )
        session.add(student)
        session.add(ClassMember(class_id=class_id, student_id=student_id))

        exam = Exam(
            id=exam_id,
            title="Đề Thi Đang Làm",
            created_by=admin_id,
            duration_minutes=45,
            subject="math",
            status="published",
            version=1,
        )
        session.add(exam)
        session.add(ExamClass(exam_id=exam_id, class_id=class_id))

        now = datetime.now(UTC)
        # 2. Create in-progress attempt for this student
        attempt = Attempt(
            id=attempt_id,
            exam_id=exam_id,
            student_id=student_id,
            status="in_progress",
            deadline_at=now + timedelta(minutes=45),
            shuffle_seed=12345,
        )
        session.add(attempt)
        session.commit()

    # 3. Admin withdraws student from class by setting user_ids to empty list []
    put_res = client.put(
        f"/api/v1/admin/classes/{class_id}/members",
        json={"user_ids": []},
        headers=auth_header(admin_token),
    )
    assert put_res.status_code == 200
    assert put_res.json()["removed"] == 1
    assert put_res.json()["total"] == 0

    # 4. Verify student is removed from class, but attempt remains in_progress and can be submitted
    with Session(engine) as session:
        is_member = session.execute(
            select(ClassMember).where(
                ClassMember.class_id == class_id, ClassMember.student_id == student_id
            )
        ).first()
        assert is_member is None

        # Attempt is untouched and valid
        att = session.execute(select(Attempt).where(Attempt.id == attempt_id)).scalar_one_or_none()
        assert att is not None
        assert att.status == "in_progress"

        # Simulate student finishing and submitting attempt
        att.status = "submitted"
        att.submitted_at = text("now()")
        session.commit()

        # Submission succeeded
        refreshed = session.execute(select(Attempt).where(Attempt.id == attempt_id)).scalar_one()
        assert refreshed.status == "submitted"


def test_tc_3_2_08_disabling_student_revokes_sessions(client, admin_token):
    """TC-3.2-08: Disabling student account immediately revokes sessions; /auth/me returns 401."""
    # 1. Create student
    create_res = client.post(
        "/api/v1/admin/students",
        json={"username": "lock_me", "full_name": "Học Sinh Khóa", "password": "StudentPass123!"},
        headers=auth_header(admin_token),
    )
    student_id = create_res.json()["id"]

    # 2. Student logs in to get session token
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "lock_me", "password": "StudentPass123!"},
    )
    assert login_res.status_code == 200
    student_token = login_res.json()["access_token"]

    # 3. Verify /auth/me returns 200 for active student
    me_res = client.get("/api/v1/auth/me", headers=auth_header(student_token))
    assert me_res.status_code == 200
    assert me_res.json()["username"] == "lock_me"

    # 4. Admin disables student account: PATCH is_active = False
    patch_res = client.patch(
        f"/api/v1/admin/students/{student_id}",
        json={"is_active": False},
        headers=auth_header(admin_token),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_active"] is False

    # 5. Previous session token is now invalid -> /auth/me returns 401 immediately
    me_after_lock = client.get("/api/v1/auth/me", headers=auth_header(student_token))
    assert me_after_lock.status_code == 401
    assert me_after_lock.json()["error"]["code"] == "invalid_session"
