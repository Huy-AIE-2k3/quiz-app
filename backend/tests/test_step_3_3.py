"""Tests for Step 3.3: Batch Student CSV Import (Two-Phase Protocol).

Verifies:
    TC-3.3-01: UTF-8 BOM + ';' delimiter parsed accurately with Vietnamese diacritics.
    TC-3.3-02: Windows-1258 (cp1258) decoded without garbled text ('Nguyễn Văn Ánh').
    TC-3.3-03: Dry-run reports exact row errors; database remains untouched (0 new students).
    TC-3.3-04: Atomic commit: 1 row error among 40 rolls back 100% (0 new students created).
    TC-3.3-05: Duplicate username in same file flags rows with username_duplicate_in_file.
    TC-3.3-06: Strict limits: 501 rows -> 422, >1 MB -> 413, empty -> 400, missing headers -> 400.
    TC-3.3-07: CSV injection: cells starting with =, +, -, @ prepended with single quote in export.
    TC-3.3-08: Quoted cells with commas and escaped quotes parsed accurately ('Trần, Văn "A"').
    TC-3.3-09: Auto-generated passwords: 1,000 samples exclude 0OIl1 and contain letters + digits.
    TC-3.3-10: Non-existent class code reported as class_not_found; class is never auto-created.
"""

import io
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.core.security import generate_random_password, hash_password
from app.db.session import get_engine
from app.main import create_app
from app.models import Class, ClassMember, User


@pytest.fixture(autouse=True)
def clean_db():
    """Cleans up database tables between test runs."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 3.3 tests: {exc}")

    with Session(engine) as session:
        session.execute(text("TRUNCATE TABLE sessions CASCADE"))
        session.execute(text("TRUNCATE TABLE class_members CASCADE"))
        session.execute(text("TRUNCATE TABLE classes CASCADE"))
        session.execute(text("TRUNCATE TABLE users CASCADE"))
        session.commit()

    yield

    with Session(engine) as session:
        session.execute(text("TRUNCATE TABLE sessions CASCADE"))
        session.execute(text("TRUNCATE TABLE class_members CASCADE"))
        session.execute(text("TRUNCATE TABLE classes CASCADE"))
        session.execute(text("TRUNCATE TABLE users CASCADE"))
        session.commit()


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_token(client):
    engine = get_engine()
    admin_id = uuid.uuid4()
    with Session(engine) as session:
        admin = User(
            id=admin_id,
            username="admin_step33",
            full_name="Admin Step 33",
            hashed_password=hash_password("AdminSecure123!"),
            role="admin",
            is_active=True,
        )
        session.add(admin)
        session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_step33", "password": "AdminSecure123!"},
    )
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_tc_3_3_01_utf8_bom_and_semicolon(client, admin_token):
    """TC-3.3-01: UTF-8 BOM + ';' delimiter parsed accurately with Vietnamese diacritics."""
    engine = get_engine()
    class_id = uuid.uuid4()
    with Session(engine) as session:
        session.add(Class(id=class_id, code="10A1", name="Lớp 10A1", academic_year=2026))
        session.commit()

    csv_text = (
        "\ufeffHọ và tên;Tên đăng nhập;Mật khẩu;Mã lớp\r\n"
        "Nguyễn Thị Hoa;hoa.nt;HoaPass123!;10A1\r\n"
        "Trần Đức Nam;nam.td;NamPass123!;10A1\r\n"
    )
    csv_bytes = csv_text.encode("utf-8")

    files = {"file": ("students_excel.csv", io.BytesIO(csv_bytes), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=false&auto_generate_passwords=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["total_rows"] == 2
    assert data["valid_rows"] == 2
    assert data["created_count"] == 2
    assert data["can_commit"] is True

    # Verify database records
    with Session(engine) as session:
        hoa = session.execute(select(User).where(User.username == "hoa.nt")).scalar_one()
        assert hoa.full_name == "Nguyễn Thị Hoa"
        nam = session.execute(select(User).where(User.username == "nam.td")).scalar_one()
        assert nam.full_name == "Trần Đức Nam"

        members = (
            session.execute(select(ClassMember).where(ClassMember.class_id == class_id))
            .scalars()
            .all()
        )
        assert len(members) == 2


def test_tc_3_3_02_windows_1258_vietnamese_ansi(client, admin_token):
    """TC-3.3-02: Windows-1258 (cp1258) decoded without garbled text ('Nguyễn Văn Ánh')."""
    engine = get_engine()
    # In Windows-1258, combining diacritics represent tone marks on vowels
    header = "ho_ten,username,password\r\n"
    row = "Nguy\xea\u0303n V\u0103n \xc1nh,anh.nv,AnhPass123!\r\n"
    csv_bytes = (header + row).encode("cp1258")

    files = {"file": ("students_ansi.csv", io.BytesIO(csv_bytes), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200, res.text
    data = res.json()
    assert data["valid_rows"] == 1
    assert data["created_count"] == 1

    with Session(engine) as session:
        user = session.execute(select(User).where(User.username == "anh.nv")).scalar_one()
        assert user.full_name == "Nguyễn Văn Ánh"


def test_tc_3_3_03_dry_run_reports_errors_db_unchanged(client, admin_token):
    """TC-3.3-03: Dry-run reports exact row errors; database remains untouched."""
    engine = get_engine()
    csv_text = (
        "Họ tên,Tên đăng nhập,Mật khẩu\r\n"
        "  ,invalid_name,Pass123!\r\n"  # row 2: name_empty
        "Lê Văn B,user with spaces,Pass123!\r\n"  # row 3: username_invalid
        "Trần Văn C,user_no_pass,\r\n"  # row 4: password_required (auto_generate_passwords=false)
        "Phạm Văn D,user_valid_d,Pass123!\r\n"  # row 5: valid
        "Hoàng Thị E,user_valid_e,Pass123!\r\n"  # row 6: valid
    )
    files = {"file": ("test_dry_run.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=true&auto_generate_passwords=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total_rows"] == 5
    assert data["valid_rows"] == 2
    assert data["error_rows"] == 3
    assert data["can_commit"] is False

    rows = data["rows"]
    assert rows[0]["errors"] == ["name_empty"]
    assert rows[1]["errors"] == ["username_invalid"]
    assert rows[2]["errors"] == ["password_required"]
    assert rows[3]["status"] == "valid"
    assert rows[4]["status"] == "valid"

    # Verify zero student users created in database
    with Session(engine) as session:
        student_count = session.execute(select(User).where(User.role == "student")).scalars().all()
        assert len(student_count) == 0


def test_tc_3_3_04_atomic_commit_rollback_on_single_error(client, admin_token):
    """TC-3.3-04: Atomic commit: 1 row error among 40 rolls back 100% (0 new students)."""
    engine = get_engine()
    # Pre-create duplicate user for row 30
    with Session(engine) as session:
        session.add(
            User(
                username="student_dup_30",
                full_name="Existing Student 30",
                hashed_password=hash_password("Pass123!"),
                role="student",
                is_active=True,
            )
        )
        session.commit()

    # Generate 40 rows where row 30 is duplicate username
    lines = ["Họ và tên,Tên đăng nhập,Mật khẩu"]
    for i in range(1, 41):
        if i == 30:
            lines.append("Học Sinh Ba Mươi,student_dup_30,Pass123!")
        else:
            lines.append(f"Học Sinh Thứ {i},student_test_{i:02d},Pass123!")
    csv_bytes = "\r\n".join(lines).encode("utf-8")

    files = {"file": ("batch_40.csv", io.BytesIO(csv_bytes), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 422
    err_json = res.json()
    assert err_json["error"]["code"] == "csv_import_validation_failed"

    details = err_json["error"]["details"]
    assert details["can_commit"] is False
    assert details["error_rows"] == 1
    # Check row 30 (Excel row 31)
    row_30 = next(r for r in details["rows"] if r["row_number"] == 31)
    assert "username_taken" in row_30["errors"]

    # Verify zero new students created in DB (only the 1 pre-existing student remains)
    with Session(engine) as session:
        students = session.execute(select(User).where(User.role == "student")).scalars().all()
        assert len(students) == 1
        assert students[0].username == "student_dup_30"


def test_tc_3_3_05_duplicate_username_within_file(client, admin_token):
    """TC-3.3-05: Duplicate username in same file flags rows with username_duplicate_in_file."""
    csv_text = (
        "Họ tên,Tên đăng nhập,Mật khẩu\r\n"
        "Nguyễn Văn A,dup.user,Pass123!\r\n"  # row 2
        "Trần Văn B,other.user,Pass123!\r\n"  # row 3
        "Lê Văn C,dup.user,Pass123!\r\n"  # row 4 (duplicate of row 2)
    )
    files = {"file": ("file_dup.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["error_rows"] == 2

    # Both row 2 and row 4 flagged with username_duplicate_in_file
    assert "username_duplicate_in_file" in data["rows"][0]["errors"]
    assert "username_duplicate_in_file" in data["rows"][2]["errors"]
    assert data["rows"][1]["status"] == "valid"


def test_tc_3_3_06_csv_limits_enforcement(client, admin_token):
    """TC-3.3-06: Limits: 501 rows -> 422, >1 MB -> 413, empty -> 400, missing headers -> 400."""
    # 1. 501 rows -> 422 csv_too_many_rows
    lines = ["Họ và tên,Tên đăng nhập,Mật khẩu"] + [
        f"Học Sinh {i},student_{i},Pass123!" for i in range(501)
    ]
    csv_501 = "\r\n".join(lines).encode("utf-8")
    res_501 = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files={"file": ("too_many.csv", io.BytesIO(csv_501), "text/csv")},
        headers=auth_header(admin_token),
    )
    assert res_501.status_code == 422
    assert res_501.json()["error"]["code"] == "csv_too_many_rows"

    # 2. > 1 MB -> 413 csv_file_too_large or request_entity_too_large
    large_bytes = b"A" * (1024 * 1024 + 50)
    res_large = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files={"file": ("large.csv", io.BytesIO(large_bytes), "text/csv")},
        headers=auth_header(admin_token),
    )
    assert res_large.status_code == 413
    assert res_large.json()["error"]["code"] in ("csv_file_too_large", "request_entity_too_large")

    # 3. Empty file -> 400 csv_empty
    res_empty = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files={"file": ("empty.csv", io.BytesIO(b"   \r\n   "), "text/csv")},
        headers=auth_header(admin_token),
    )
    assert res_empty.status_code == 400
    assert res_empty.json()["error"]["code"] == "csv_empty"

    # 4. Missing headers -> 400 csv_missing_header
    bad_header = b"Cot1,Cot2,Cot3\r\nVal1,Val2,Val3\r\n"
    res_bad_header = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files={"file": ("bad_header.csv", io.BytesIO(bad_header), "text/csv")},
        headers=auth_header(admin_token),
    )
    assert res_bad_header.status_code == 400
    assert res_bad_header.json()["error"]["code"] == "csv_missing_header"


def test_tc_3_3_07_csv_injection_formula_escaping(client, admin_token):
    """TC-3.3-07: CSV injection: formula triggers (=, +, -, @) prepended with ' in export."""
    csv_text = (
        "Họ và tên,Tên đăng nhập,Mật khẩu\r\n"
        '=HYPERLINK("http://evil.com"),user_inj1,Pass123!\r\n'
        "+1234567890,user_inj2,Pass123!\r\n"
        "-cmd|' /C calc'!A0,user_inj3,Pass123!\r\n"
        "@SUM(1+1),user_inj4,Pass123!\r\n"
    )
    files = {"file": ("injection.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["created_count"] == 4
    csv_export = data["csv_export_content"]
    assert csv_export is not None
    assert csv_export.startswith("\ufeff")  # Starts with UTF-8 BOM

    # Verify formula cells have leading single quote in CSV export
    assert "'=HYPERLINK" in csv_export
    assert "'+1234567890" in csv_export
    assert "'-cmd" in csv_export
    assert "'@SUM" in csv_export


def test_tc_3_3_08_quoted_cells_with_commas_and_quotes(client, admin_token):
    """TC-3.3-08: Quoted cells with commas and escaped quotes parsed accurately."""
    engine = get_engine()
    csv_text = 'Họ và tên,Tên đăng nhập,Mật khẩu\r\n"Trần, Văn ""A""",tran.va,Pass123!\r\n'
    files = {"file": ("quotes.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=false",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    with Session(engine) as session:
        user = session.execute(select(User).where(User.username == "tran.va")).scalar_one()
        assert user.full_name == 'Trần, Văn "A"'


def test_tc_3_3_09_auto_generated_passwords_format():
    """TC-3.3-09: Auto passwords: 1,000 samples exclude 0OIl1 and contain letters + digits."""
    ambiguous_chars = set("0OIl1")
    for _ in range(1000):
        pwd = generate_random_password(length=8)
        assert len(pwd) == 8
        assert not any(c in ambiguous_chars for c in pwd)
        assert any(c.isalpha() for c in pwd)
        assert any(c.isdigit() for c in pwd)


def test_tc_3_3_10_non_existent_class_code_not_found(client, admin_token):
    """TC-3.3-10: Non-existent class code reported as class_not_found; class is never created."""
    engine = get_engine()
    csv_text = "Họ và tên,Tên đăng nhập,Mật khẩu,Mã lớp\r\nNguyễn Văn An,an.nv,Pass123!,ZZZ\r\n"
    files = {"file": ("class_check.csv", io.BytesIO(csv_text.encode("utf-8")), "text/csv")}
    res = client.post(
        "/api/v1/admin/students/import?dry_run=true",
        files=files,
        headers=auth_header(admin_token),
    )
    assert res.status_code == 200
    data = res.json()
    assert data["can_commit"] is False
    assert data["rows"][0]["errors"] == ["class_not_found"]

    # Verify class 'ZZZ' is NOT auto-created
    with Session(engine) as session:
        found_class = session.execute(select(Class).where(Class.code == "ZZZ")).scalar_one_or_none()
        assert found_class is None
