"""Tests for Step 3.1: Admin Class Management API.

Verifies:
    TC-3.1-01: Create valid class -> 201; code is stored in UPPERCASE.
    TC-3.1-02: Duplicate class code -> 409 class_code_taken.
    TC-3.1-03: In-use class cannot be hard deleted -> 409 class_in_use;
               archiving hides it from default list.
    TC-3.1-04: Search with special characters (% and _) matches literal characters.
    TC-3.1-05: Pagination boundary validation (limit=0, limit=101, offset < 0 -> 422).
    TC-3.1-06: Query performance: listing 50 classes executes <= 3 SQL statements (no N+1).
    TC-3.1-07: Optimistic concurrency conflict: concurrent PATCH with same version -> 409.
"""

import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import event, text
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.session import get_engine
from app.main import create_app
from app.models import Class, Exam, ExamClass, User


@pytest.fixture(autouse=True)
def clean_db():
    """Cleans up database tables between test runs."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 3.1 tests: {exc}")

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
            username="admin_step31",
            full_name="Quản Trị Viên 3.1",
            hashed_password=hash_password("AdminSecurePassword123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_step31", "password": "AdminSecurePassword123!"},
    )
    assert res.status_code == 200
    return res.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_tc_3_1_01_create_class_uppercase_code(client, admin_token):
    """TC-3.1-01: Create valid class -> 201; code is automatically converted to UPPERCASE."""
    payload = {
        "code": "10a1",
        "name": "Lớp 10 Chuyên Toán A1",
        "academic_year": 2026,
        "subject": "toan",
    }

    res = client.post("/api/v1/admin/classes", json=payload, headers=auth_header(admin_token))
    assert res.status_code == 201
    data = res.json()
    assert data["code"] == "10A1"  # Normalized to uppercase
    assert data["name"] == "Lớp 10 Chuyên Toán A1"
    assert data["academic_year"] == 2026
    assert data["subject"] == "toan"
    assert data["is_archived"] is False
    assert data["version"] == 1
    assert data["student_count"] == 0
    assert data["exam_count"] == 0


def test_tc_3_1_02_duplicate_class_code(client, admin_token):
    """TC-3.1-02: Duplicate class code -> 409 class_code_taken."""
    payload1 = {
        "code": "10a1",
        "name": "Lớp 10A1",
        "academic_year": 2026,
        "subject": "toan",
    }
    res1 = client.post("/api/v1/admin/classes", json=payload1, headers=auth_header(admin_token))
    assert res1.status_code == 201

    payload2 = {
        "code": "10A1",  # Same code in uppercase
        "name": "Lớp 10A1 Thứ Hai",
        "academic_year": 2026,
        "subject": "tin",
    }
    res2 = client.post("/api/v1/admin/classes", json=payload2, headers=auth_header(admin_token))
    assert res2.status_code == 409
    err = res2.json()["error"]
    assert err["code"] == "class_code_taken"
    assert "10A1" in err["message"]


def test_tc_3_1_03_in_use_class_cannot_be_deleted(client, admin_token):
    """TC-3.1-03: In-use class cannot be deleted (409); archiving hides it from default list."""
    engine = get_engine()
    class_id = uuid.uuid4()
    with Session(engine) as session:
        # 1. Create class
        cls_obj = Class(
            id=class_id,
            code="11TIN",
            name="Lớp 11 Tin Học",
            academic_year=2026,
            subject="tin",
            version=1,
        )
        session.add(cls_obj)

        admin_id = session.execute(
            text("SELECT id FROM users WHERE username = 'admin_step31'")
        ).scalar()

        # 2. Create exam assigned to this class
        exam = Exam(
            title="Đề Kiểm Tra 1 Tiết Tin Học",
            created_by=admin_id,
            duration_minutes=45,
            subject="computer_science",
            status="published",
            version=1,
        )
        session.add(exam)
        session.flush()

        exam_class = ExamClass(exam_id=exam.id, class_id=class_id)
        session.add(exam_class)
        session.commit()

    # 3. Attempt to hard DELETE class in use -> 409 class_in_use
    del_res = client.delete(f"/api/v1/admin/classes/{class_id}", headers=auth_header(admin_token))
    assert del_res.status_code == 409
    err = del_res.json()["error"]
    assert err["code"] == "class_in_use"

    # 4. Soft-delete by setting is_archived = True
    patch_res = client.patch(
        f"/api/v1/admin/classes/{class_id}",
        json={"is_archived": True, "version": 1},
        headers=auth_header(admin_token),
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["is_archived"] is True
    assert patch_res.json()["version"] == 2

    # 5. Default GET /classes list hides archived classes
    list_res = client.get("/api/v1/admin/classes", headers=auth_header(admin_token))
    assert list_res.status_code == 200
    class_ids = [item["id"] for item in list_res.json()["items"]]
    assert str(class_id) not in class_ids

    # 6. GET /classes?include_archived=true includes archived classes
    list_archived = client.get(
        "/api/v1/admin/classes?include_archived=true",
        headers=auth_header(admin_token),
    )
    assert list_archived.status_code == 200
    archived_ids = [item["id"] for item in list_archived.json()["items"]]
    assert str(class_id) in archived_ids


def test_tc_3_1_04_search_special_characters_sql_like(client, admin_token):
    """TC-3.1-04: Search with % and _ matches literal characters without wildcards."""
    engine = get_engine()
    with Session(engine) as session:
        session.add(
            Class(
                code="SPECIAL_1",
                name="Lớp 100% Chuyên",
                academic_year=2026,
                subject="toan",
                version=1,
            )
        )
        session.add(
            Class(
                code="SPECIAL_2",
                name="Lớp_Đặc_Biệt",
                academic_year=2026,
                subject="tin",
                version=1,
            )
        )
        session.add(
            Class(
                code="NORMAL",
                name="Lớp Bình Thường",
                academic_year=2026,
                subject="both",
                version=1,
            )
        )
        session.commit()

    # Search literal "%"
    res_percent = client.get("/api/v1/admin/classes?q=%", headers=auth_header(admin_token))
    assert res_percent.status_code == 200
    items_percent = res_percent.json()["items"]
    assert len(items_percent) == 1
    assert items_percent[0]["name"] == "Lớp 100% Chuyên"

    # Search literal "_"
    res_underscore = client.get(
        "/api/v1/admin/classes?q=Lớp_Đặc_Biệt", headers=auth_header(admin_token)
    )
    assert res_underscore.status_code == 200
    items_underscore = res_underscore.json()["items"]
    assert len(items_underscore) == 1
    assert items_underscore[0]["name"] == "Lớp_Đặc_Biệt"


def test_tc_3_1_05_pagination_boundary_validation(client, admin_token):
    """TC-3.1-05: Pagination boundary validation (limit=0, limit=101, offset < 0 -> 422)."""
    # 1. limit=0 -> 422
    res_l0 = client.get("/api/v1/admin/classes?limit=0", headers=auth_header(admin_token))
    assert res_l0.status_code == 422

    # 2. limit=101 -> 422
    res_l101 = client.get("/api/v1/admin/classes?limit=101", headers=auth_header(admin_token))
    assert res_l101.status_code == 422

    # 3. offset < 0 -> 422
    res_neg_off = client.get("/api/v1/admin/classes?offset=-1", headers=auth_header(admin_token))
    assert res_neg_off.status_code == 422

    # 4. offset > total -> valid empty list (not error)
    res_large_off = client.get(
        "/api/v1/admin/classes?offset=99999", headers=auth_header(admin_token)
    )
    assert res_large_off.status_code == 200
    assert res_large_off.json()["items"] == []


def test_tc_3_1_06_query_performance_no_n_plus_one(client, admin_token):
    """TC-3.1-06: Listing 50 classes with member and exam counts executes <= 3 SQL statements."""
    engine = get_engine()
    with Session(engine) as session:
        # Create 50 classes
        for i in range(50):
            cls = Class(
                code=f"PERF_{i:02d}",
                name=f"Lớp Hiệu Năng {i}",
                academic_year=2026,
                subject="both",
                version=1,
            )
            session.add(cls)
        session.commit()

    # Track SQL execution statements
    query_count = 0

    def query_listener(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        # Ignore transaction setup/rollback queries
        stmt_lower = statement.strip().lower()
        if stmt_lower.startswith(("select", "insert", "update", "delete")):
            query_count += 1

    event.listen(engine, "before_cursor_execute", query_listener)

    try:
        res = client.get("/api/v1/admin/classes?limit=50", headers=auth_header(admin_token))
        assert res.status_code == 200
        data = res.json()
        assert len(data["items"]) == 50

        # Query count must be <= 3 (auth check, total count, rows+subqueries)
        assert query_count <= 3, f"Detected N+1 query problem! Query count: {query_count}"
    finally:
        event.remove(engine, "before_cursor_execute", query_listener)


def test_tc_3_1_07_optimistic_concurrency_conflict(client, admin_token):
    """TC-3.1-07: Concurrent update with same version -> one 200, other 409 version_conflict."""
    # 1. Create class
    create_res = client.post(
        "/api/v1/admin/classes",
        json={"code": "12CONC", "name": "Lớp Đồng Thời", "academic_year": 2026, "subject": "tin"},
        headers=auth_header(admin_token),
    )
    assert create_res.status_code == 201
    class_id = create_res.json()["id"]
    version = create_res.json()["version"]
    assert version == 1

    # 2. First update with version 1 -> succeeds, increments to version 2
    update_res1 = client.patch(
        f"/api/v1/admin/classes/{class_id}",
        json={"name": "Lớp Đồng Thời (Sửa Lần 1)", "version": 1},
        headers=auth_header(admin_token),
    )
    assert update_res1.status_code == 200
    assert update_res1.json()["version"] == 2

    # 3. Second update still using version 1 -> rejected with 409 version_conflict
    update_res2 = client.patch(
        f"/api/v1/admin/classes/{class_id}",
        json={"name": "Lớp Đồng Thời (Sửa Lần 2 Đè Lên)", "version": 1},
        headers=auth_header(admin_token),
    )
    assert update_res2.status_code == 409
    err = update_res2.json()["error"]
    assert err["code"] == "version_conflict"
    assert err["details"]["current_version"] == 2
    assert err["details"]["provided_version"] == 1
