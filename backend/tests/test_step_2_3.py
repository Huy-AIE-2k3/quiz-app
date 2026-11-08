"""Tests for Step 2.3: Authentication, Session Management, Security, and RBAC.

Verifies:
    TC-2.3-01: Valid login returns token and role, /auth/me returns identity
    TC-2.3-02: Timing attack mitigation: invalid vs wrong password response time delta < 35%
    TC-2.3-03: sessions table stores only SHA-256 hex digest, never raw tokens
    TC-2.3-04: Expired or revoked session returns 401
    TC-2.3-05: Rate limiting: 11th failed attempt gives 429, other user unaffected
    TC-2.3-06: 40 concurrent logins from same IP succeed safely with bounded semaphore
    TC-2.3-07: RBAC: student calling /admin/* receives 403, anonymous receives 401
    TC-2.3-08: Disabling student account revokes all active sessions immediately
    TC-2.3-09: Malformed Authorization header returns 401, never 500
    TC-2.3-10: CLI create-admin enforces constraints and handles duplicates without default accounts
"""

import concurrent.futures
import hashlib
import time
from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.cli import create_admin_user
from app.core.security import (
    clear_failed_logins,
    hash_password,
    hash_token,
)
from app.db.session import get_engine
from app.main import create_app
from app.models import Session as SessionModel
from app.models import User


@pytest.fixture(autouse=True)
def clean_db():
    """Cleans up database tables and in-memory failed login records before each test."""
    engine = get_engine()
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 2.3 tests: {exc}")

    # Wipe tables
    with Session(engine) as session:
        session.execute(text("DELETE FROM answers"))
        session.execute(text("DELETE FROM attempts"))
        session.execute(text("DELETE FROM questions"))
        session.execute(text("DELETE FROM exam_classes"))
        session.execute(text("DELETE FROM exams"))
        session.execute(text("DELETE FROM class_members"))
        session.execute(text("DELETE FROM classes"))
        session.execute(text("DELETE FROM sessions"))
        session.execute(text("DELETE FROM audit_logs"))
        session.execute(text("DELETE FROM files"))
        session.execute(text("DELETE FROM users"))
        session.commit()

    # Clear rate limiter cache
    clear_failed_logins("127.0.0.1", "testuser")
    clear_failed_logins("192.168.1.100", "testuser_fail")
    clear_failed_logins("192.168.1.100", "testuser_valid")

    yield


@pytest.fixture
def client():
    """Provides TestClient with standard app configuration."""
    app = create_app()
    return TestClient(app, raise_server_exceptions=False)


def test_tc_2_3_01_valid_login_and_me(client):
    """TC-2.3-01: Valid login returns token and role; /auth/me returns identity."""
    engine = get_engine()
    with Session(engine) as session:
        user = User(
            username="student01",
            full_name="Nguyen Van A",
            hashed_password=hash_password("SuperSecret123!"),
            role="student",
            is_active=True,
        )
        session.add(user)
        session.commit()

    # 1. Login
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "student01", "password": "SuperSecret123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["role"] == "student"
    assert data["username"] == "student01"
    assert data["full_name"] == "Nguyen Van A"
    assert "expires_at" in data

    token = data["access_token"]

    # 2. Get profile via /auth/me
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["username"] == "student01"
    assert me_data["role"] == "student"


def test_tc_2_3_02_timing_attack_mitigation(client):
    """TC-2.3-02: Non-existent username vs wrong password response times are comparable."""
    engine = get_engine()
    with Session(engine) as session:
        user = User(
            username="realuser",
            full_name="Real User",
            hashed_password=hash_password("RealPassword123!"),
            role="student",
            is_active=True,
        )
        session.add(user)
        session.commit()

    # Measure non-existent user timing (runs verify_dummy_password)
    times_non_existent = []
    for _ in range(5):
        t0 = time.perf_counter()
        client.post(
            "/api/v1/auth/login",
            json={"username": "fakeuser_non_existent", "password": "WrongPassword123!"},
        )
        times_non_existent.append(time.perf_counter() - t0)

    # Measure real user with wrong password
    times_wrong_pw = []
    for _ in range(5):
        t0 = time.perf_counter()
        client.post(
            "/api/v1/auth/login",
            json={"username": "realuser", "password": "WrongPassword123!"},
        )
        times_wrong_pw.append(time.perf_counter() - t0)

    median_non_existent = sorted(times_non_existent)[len(times_non_existent) // 2]
    median_wrong_pw = sorted(times_wrong_pw)[len(times_wrong_pw) // 2]

    # Relative difference should not exceed 35%
    max_val = max(median_non_existent, median_wrong_pw)
    diff = abs(median_non_existent - median_wrong_pw) / max_val
    assert diff < 0.35, f"Timing difference too large: {diff:.2%}"


def test_tc_2_3_03_sessions_table_stores_only_sha256_hash(client):
    """TC-2.3-03: sessions table never stores raw token, only sha256 hex digest."""
    engine = get_engine()
    with Session(engine) as session:
        user = User(
            username="student_tc3",
            full_name="Student Three",
            hashed_password=hash_password("PasswordTC3!123"),
            role="student",
            is_active=True,
        )
        session.add(user)
        session.commit()

    res = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc3", "password": "PasswordTC3!123"},
    )
    assert res.status_code == 200
    raw_token = res.json()["access_token"]
    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Query DB sessions directly
    with Session(engine) as session:
        db_sessions = session.execute(select(SessionModel)).scalars().all()
        assert len(db_sessions) == 1
        stored_hash = db_sessions[0].token_hash

        # Stored hash must match SHA-256 of raw token
        assert stored_hash == expected_hash
        # Raw token must NEVER equal stored hash
        assert raw_token != stored_hash


def test_tc_2_3_04_expired_or_revoked_session(client):
    """TC-2.3-04: Expired or revoked session returns 401."""
    engine = get_engine()
    with Session(engine) as session:
        user = User(
            username="student_tc4",
            full_name="Student Four",
            hashed_password=hash_password("PasswordTC4!123"),
            role="student",
            is_active=True,
        )
        session.add(user)
        session.commit()

    # Log in
    res = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc4", "password": "PasswordTC4!123"},
    )
    token = res.json()["access_token"]

    # 1. Expire session artificially
    with Session(engine) as session:
        sess = session.execute(
            select(SessionModel).where(SessionModel.token_hash == hash_token(token))
        ).scalar_one()
        sess.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        session.commit()

    # Calling /auth/me returns 401
    res_expired = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_expired.status_code == 401
    assert res_expired.json()["error"]["code"] == "session_expired"

    # 2. Revoked session
    # Log in again to get fresh session
    res2 = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc4", "password": "PasswordTC4!123"},
    )
    token2 = res2.json()["access_token"]

    # Revoke (logout)
    logout_res = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert logout_res.status_code == 200

    # Next call returns 401
    res_revoked = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token2}"})
    assert res_revoked.status_code == 401
    assert res_revoked.json()["error"]["code"] == "invalid_session"


def test_tc_2_3_05_rate_limiting_failed_attempts(client):
    """TC-2.3-05: 11th failed attempt gives 429; other username from same IP unaffected."""
    engine = get_engine()
    with Session(engine) as session:
        u_fail = User(
            username="target_user",
            full_name="Target User",
            hashed_password=hash_password("CorrectPass123!"),
            role="student",
            is_active=True,
        )
        u_other = User(
            username="other_user",
            full_name="Other User",
            hashed_password=hash_password("OtherPass123!"),
            role="student",
            is_active=True,
        )
        session.add_all([u_fail, u_other])
        session.commit()

    fake_ip = "192.168.1.55"
    headers = {"X-Forwarded-For": fake_ip}

    # 1. 10 failed login attempts for target_user
    for _ in range(10):
        res = client.post(
            "/api/v1/auth/login",
            json={"username": "target_user", "password": "WrongPassword!"},
            headers=headers,
        )
        assert res.status_code == 401

    # 2. 11th failed attempt returns 429 Rate Limited
    res_blocked = client.post(
        "/api/v1/auth/login",
        json={"username": "target_user", "password": "WrongPassword!"},
        headers=headers,
    )
    assert res_blocked.status_code == 429
    assert res_blocked.json()["error"]["code"] == "rate_limited"

    # 3. other_user from same IP logs in successfully (not blocked!)
    res_other = client.post(
        "/api/v1/auth/login",
        json={"username": "other_user", "password": "OtherPass123!"},
        headers=headers,
    )
    assert res_other.status_code == 200
    assert res_other.json()["username"] == "other_user"


def test_tc_2_3_06_concurrent_logins_safe_memory(client):
    """TC-2.3-06: 40 students logging in concurrently from same IP succeed safely."""
    engine = get_engine()
    with Session(engine) as session:
        for i in range(40):
            u = User(
                username=f"student_c_{i:02d}",
                full_name=f"Student Concurrency {i}",
                hashed_password=hash_password("Password123!Safe"),
                role="student",
                is_active=True,
            )
            session.add(u)
        session.commit()

    def do_login(idx: int):
        return client.post(
            "/api/v1/auth/login",
            json={"username": f"student_c_{idx:02d}", "password": "Password123!Safe"},
            headers={"X-Forwarded-For": "10.0.0.1"},
        )

    # 40 concurrent workers
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(do_login, i) for i in range(40)]
        results = [f.result() for f in futures]

    assert all(r.status_code == 200 for r in results)
    tokens = [r.json()["access_token"] for r in results]
    assert len(set(tokens)) == 40  # 40 unique tokens generated


def test_tc_2_3_07_rbac_route_protection(client):
    """TC-2.3-07: Student calling /admin/* gets 403; anonymous gets 401."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="admin_rbac",
            full_name="Admin RBAC",
            hashed_password=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        student = User(
            username="student_rbac",
            full_name="Student RBAC",
            hashed_password=hash_password("StudentPass123!"),
            role="student",
            is_active=True,
        )
        session.add_all([admin, student])
        session.commit()

    admin_token = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_rbac", "password": "AdminPass123!"},
    ).json()["access_token"]

    student_token = client.post(
        "/api/v1/auth/login",
        json={"username": "student_rbac", "password": "StudentPass123!"},
    ).json()["access_token"]

    # 1. Anonymous calling /admin/dashboard -> 401
    res_anon_admin = client.get("/api/v1/admin/dashboard")
    assert res_anon_admin.status_code == 401

    # 2. Student calling /admin/dashboard -> 403 Forbidden
    res_student_admin = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student_admin.status_code == 403
    assert res_student_admin.json()["error"]["code"] == "forbidden"

    # 3. Admin calling /admin/dashboard -> 200
    res_admin_ok = client.get(
        "/api/v1/admin/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_ok.status_code == 200

    # 4. Admin calling /student/dashboard -> 403 Forbidden
    res_admin_student = client.get(
        "/api/v1/student/dashboard",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res_admin_student.status_code == 403

    # 5. Student calling /student/dashboard -> 200 OK
    res_student_ok = client.get(
        "/api/v1/student/dashboard",
        headers={"Authorization": f"Bearer {student_token}"},
    )
    assert res_student_ok.status_code == 200


def test_tc_2_3_08_disabling_user_revokes_all_sessions(client):
    """TC-2.3-08: Disabling student account revokes all active sessions immediately."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="admin_tc8",
            full_name="Admin Eight",
            hashed_password=hash_password("AdminPass123!"),
            role="admin",
            is_active=True,
        )
        student = User(
            username="student_tc8",
            full_name="Student Eight",
            hashed_password=hash_password("StudentPass123!"),
            role="student",
            is_active=True,
        )
        session.add_all([admin, student])
        session.commit()
        student_id = student.id

    admin_token = client.post(
        "/api/v1/auth/login",
        json={"username": "admin_tc8", "password": "AdminPass123!"},
    ).json()["access_token"]

    # Student logs in twice on two different devices
    t1 = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc8", "password": "StudentPass123!"},
        headers={"User-Agent": "Device-Phone"},
    ).json()["access_token"]

    t2 = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc8", "password": "StudentPass123!"},
        headers={"User-Agent": "Device-Laptop"},
    ).json()["access_token"]

    # Both tokens are initially valid
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}
    assert client.get("/api/v1/auth/me", headers=h1).status_code == 200
    assert client.get("/api/v1/auth/me", headers=h2).status_code == 200

    # Admin disables student account
    disable_res = client.post(
        f"/api/v1/admin/users/{student_id}/disable",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert disable_res.status_code == 200
    assert disable_res.json()["revoked_sessions"] == 2

    # Both sessions immediately revoked -> 401
    assert client.get("/api/v1/auth/me", headers=h1).status_code == 401
    assert client.get("/api/v1/auth/me", headers=h2).status_code == 401

    # Student cannot log in again -> 403 account_disabled
    login_attempt = client.post(
        "/api/v1/auth/login",
        json={"username": "student_tc8", "password": "StudentPass123!"},
    )
    assert login_attempt.status_code == 403
    assert login_attempt.json()["error"]["code"] == "account_disabled"


def test_tc_2_3_09_malformed_authorization_header(client):
    """TC-2.3-09: Malformed Authorization header returns 401, never 500."""
    malformed_headers = [
        "Basic dXNlcjpwYXNz",
        "Bearer",
        "Bearer token1 token2",
        "RandomStringWithoutBearer",
        "Token xyz123",
    ]

    for bad_header in malformed_headers:
        res = client.get("/api/v1/auth/me", headers={"Authorization": bad_header})
        assert res.status_code == 401
        data = res.json()
        assert "error" in data
        assert data["error"]["code"] in ("invalid_token_header", "missing_credentials")


def test_tc_2_3_10_cli_create_admin_enforcement():
    """TC-2.3-10: CLI create-admin enforces constraints and handles duplicates."""
    # 1. Username too short (< 3 chars) -> rejected
    success_short_user = create_admin_user(
        username="ad",
        password="ValidPassword123!",
        full_name="Admin Short",
    )
    assert success_short_user is False

    # 2. Password too short (< 12 chars) -> rejected
    success_short_pw = create_admin_user(
        username="admin_valid",
        password="Short123!",
        full_name="Admin Short PW",
    )
    assert success_short_pw is False

    # 3. Valid creation -> succeeds
    success_valid = create_admin_user(
        username="admin_tc10",
        password="SecureLongPassword123!",
        full_name="Admin Valid Ten",
    )
    assert success_valid is True

    # 4. Duplicate creation with same username -> rejected clearly
    success_duplicate = create_admin_user(
        username="admin_tc10",
        password="AnotherLongPassword123!",
        full_name="Admin Duplicate",
    )
    assert success_duplicate is False
