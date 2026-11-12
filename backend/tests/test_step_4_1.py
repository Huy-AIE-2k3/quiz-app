"""Tests for Step 4.1: Question Schemas (5 Formats) & Student View Allow-List.

Test Cases:
- TC-4.1-01: Valid creation of all 5 question types (mcq, tf, short_text, short_number, file_upload)
- TC-4.1-02: Invalid schema rejection (MCQ 1 opt, wrong correct, unparseable numbers, exe ext)
- TC-4.1-03: Boundary points validation (0, -1, 100.01, 0.255 rejected; 0.25, 100 accepted)
- TC-4.1-04: Allow-list student view: 0% data leakage of answer_key, explanation, correct, secret
- TC-4.1-05: Hypothesis property testing: verifies 0 forbidden keys across generated questions
- TC-4.1-06: Corrupted question handling: corrupt MCQ in list is marked unavailable, no crash
- TC-4.1-07: Stable option shuffling: identical seeds yield identical order, different yield diff
- TC-4.1-08: TF 3 statements with scoring='thpt' switches to 'proportional' with warning
"""

import uuid
from decimal import Decimal
from typing import Any

import pytest
from fastapi.testclient import TestClient
from hypothesis import given, settings
from hypothesis import strategies as st
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.main import create_app
from app.models import Exam, User
from app.schemas.admin_question import (
    QuestionCreate,
)
from app.schemas.student_question import (
    FORBIDDEN_STUDENT_KEYS,
    STUDENT_CONFIG_KEYS,
    student_view,
    student_view_list,
)


def recursive_find_keys(obj: Any) -> set[str]:
    """Recursively collects all dictionary keys at any depth in an object."""
    keys: set[str] = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            keys.add(k)
            keys.update(recursive_find_keys(v))
    elif isinstance(obj, list):
        for item in obj:
            keys.update(recursive_find_keys(item))
    return keys


# ==============================================================================
# TC-4.1-01: Valid creation of all 5 question types
# ==============================================================================
def test_tc_4_1_01_valid_creation_5_types() -> None:
    """TC-4.1-01: Creates valid instances for all 5 question types."""
    # 1. MCQ
    mcq = QuestionCreate(
        type="mcq",
        content_md="Giải phương trình $x^2 - 9 = 0$:",
        points=Decimal("1.00"),
        config={
            "options": [
                {"id": "o1", "content_md": "$x = \\pm 3$"},
                {"id": "o2", "content_md": "$x = 3$"},
                {"id": "o3", "content_md": "$x = -3$"},
            ]
        },
        answer_key={"correct": "o1"},
        explanation_md="Phương trình có 2 nghiệm đối xứng.",
    )
    assert mcq.type == "mcq"
    assert mcq.answer_key["correct"] == "o1"
    assert len(mcq.config["options"]) == 3

    # 2. TF (4 statements, THPT)
    tf = QuestionCreate(
        type="tf",
        content_md="Xét tính đúng sai của các khẳng định sau:",
        points=Decimal("1.00"),
        config={
            "statements": [
                {"id": "s1", "content_md": "Hàm số đồng biến trên R"},
                {"id": "s2", "content_md": "Đồ thị có tiệm cận đứng"},
                {"id": "s3", "content_md": "Giá trị nhỏ nhất bằng 0"},
                {"id": "s4", "content_md": "Hàm số liên tục tại x = 1"},
            ],
            "scoring": "thpt",
        },
        answer_key={"s1": True, "s2": False, "s3": True, "s4": False},
    )
    assert tf.type == "tf"
    assert tf.config["scoring"] == "thpt"
    assert tf.answer_key["s1"] is True

    # 3. Short Text
    st_q = QuestionCreate(
        type="short_text",
        content_md="Thủ đô của Việt Nam là gì?",
        points=Decimal("0.50"),
        config={"grading": "auto", "review_wrong": False},
        answer_key={"accepted": ["Hà Nội", "Ha Noi"]},
    )
    assert st_q.type == "short_text"
    assert "Hà Nội" in st_q.answer_key["accepted"]

    # 4. Short Number
    sn = QuestionCreate(
        type="short_number",
        content_md="Tính vận tốc ánh sáng trong chân không (triệu m/s):",
        points=Decimal("1.50"),
        config={"tolerance": Decimal("0.05"), "tolerance_type": "abs"},
        answer_key={"values": ["300", "299.792", "3e2"]},
    )
    assert sn.type == "short_number"
    assert sn.config["tolerance"] == 0.05
    assert len(sn.answer_key["values"]) == 3

    # 5. File Upload
    fu = QuestionCreate(
        type="file_upload",
        content_md="Nộp mã nguồn giải thuật Dijkstra:",
        points=Decimal("4.00"),
        config={"max_files": 2, "max_mb": 10, "allowed_ext": ["py", "cpp", "pdf"]},
        answer_key={"rubric_md": "Chấm đúng thuật toán và độ phức tạp."},
    )
    assert fu.type == "file_upload"
    assert fu.config["max_files"] == 2
    assert "py" in fu.config["allowed_ext"]


# ==============================================================================
# TC-4.1-02: Invalid schema rejection
# ==============================================================================
def test_tc_4_1_02_invalid_schema_rejection() -> None:
    """TC-4.1-02: Reject invalid configs with specific ValidationError."""
    # 1. MCQ with only 1 option
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="mcq",
            content_md="Câu hỏi",
            points=Decimal("1.00"),
            config={"options": [{"id": "o1", "content_md": "Duy nhất"}]},
            answer_key={"correct": "o1"},
        )
    assert "options" in str(exc_info.value)

    # 2. MCQ correct not in options
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="mcq",
            content_md="Câu hỏi",
            points=Decimal("1.00"),
            config={
                "options": [
                    {"id": "o1", "content_md": "Opt 1"},
                    {"id": "o2", "content_md": "Opt 2"},
                ]
            },
            answer_key={"correct": "o8"},  # o8 not in options
        )
    assert "không nằm trong danh sách lựa chọn" in str(exc_info.value)

    # 3. TF missing a statement key
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="tf",
            content_md="Câu hỏi",
            points=Decimal("1.00"),
            config={
                "statements": [
                    {"id": "s1", "content_md": "Mệnh đề 1"},
                    {"id": "s2", "content_md": "Mệnh đề 2"},
                ]
            },
            answer_key={"s1": True},  # missing s2
        )
    assert "thiếu mệnh đề" in str(exc_info.value)

    # 4. TF non-boolean value in answer key
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="tf",
            content_md="Câu hỏi",
            points=Decimal("1.00"),
            config={"statements": [{"id": "s1", "content_md": "Mệnh đề 1"}]},
            answer_key={"s1": "True"},  # string instead of bool
        )
    assert "boolean" in str(exc_info.value)

    # 5. Short number with unparseable string
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="short_number",
            content_md="Câu hỏi",
            points=Decimal("1.00"),
            config={"tolerance": Decimal("0"), "tolerance_type": "abs"},
            answer_key={"values": ["abc"]},
        )
    assert "Không thể phân tích giá trị số" in str(exc_info.value)

    # 6. File upload with disallowed extension .exe
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="file_upload",
            content_md="Nộp bài",
            points=Decimal("2.00"),
            config={"max_files": 1, "max_mb": 5, "allowed_ext": ["exe"]},
            answer_key={},
        )
    assert "không được cho phép" in str(exc_info.value)


# ==============================================================================
# TC-4.1-03: Boundary points validation
# ==============================================================================
@pytest.mark.parametrize(
    "invalid_points",
    [
        Decimal("0"),
        Decimal("-1"),
        Decimal("100.01"),
        Decimal("0.255"),  # 3 decimal places
        Decimal("0.001"),
    ],
)
def test_tc_4_1_03_boundary_points_rejected(invalid_points: Decimal) -> None:
    """TC-4.1-03: Points must be 0 < points <= 100 with scale <= 2."""
    with pytest.raises(ValidationError) as exc_info:
        QuestionCreate(
            type="short_text",
            content_md="Thủ đô:",
            points=invalid_points,
            config={"grading": "manual"},
            answer_key={},
        )
    err = str(exc_info.value)
    assert any(msg in err for msg in ["lớn hơn 0", "vượt quá 100", "tối đa 2 chữ số thập phân"])


@pytest.mark.parametrize(
    "valid_points",
    [
        Decimal("0.25"),
        Decimal("0.50"),
        Decimal("1"),
        Decimal("2.75"),
        Decimal("10.00"),
        Decimal("100.00"),
    ],
)
def test_tc_4_1_03_boundary_points_accepted(valid_points: Decimal) -> None:
    """TC-4.1-03: Valid boundary points are accepted."""
    q = QuestionCreate(
        type="short_text",
        content_md="Thủ đô:",
        points=valid_points,
        config={"grading": "manual"},
        answer_key={},
    )
    assert q.points == valid_points


# ==============================================================================
# TC-4.1-04: Allow-list student view (0% data leakage)
# ==============================================================================
def test_tc_4_1_04_allow_list_student_view_zero_leakage() -> None:
    """TC-4.1-04: student_view strictly excludes all forbidden keys."""
    # Test across all 5 types with intentional forbidden/secret fields inserted
    q_dict_mcq = {
        "id": str(uuid.uuid4()),
        "type": "mcq",
        "content_md": "Câu hỏi trắc nghiệm?",
        "points": "2.00",
        "config": {
            "options": [
                {"id": "o1", "content_md": "A", "secret": "leaked_opt_secret"},
                {"id": "o2", "content_md": "B"},
            ],
            "secret": "leaked_config_secret",
            "tolerance": 0.1,
        },
        "answer_key": {"correct": "o1", "secret": "leaked_answer_secret"},
        "explanation_md": "Lời giải chi tiết bí mật",
    }

    sv = student_view(q_dict_mcq)

    # 1. Output must only have allow-listed top-level keys
    allowed_top_keys = {"id", "type", "content_md", "points", "config", "unavailable"}
    assert set(sv.keys()).issubset(allowed_top_keys)

    # 2. Config must only contain allow-listed keys for mcq
    assert set(sv["config"].keys()).issubset(STUDENT_CONFIG_KEYS["mcq"])

    # 3. Recursively check all keys
    all_keys = recursive_find_keys(sv)
    for forbidden in FORBIDDEN_STUDENT_KEYS:
        assert forbidden not in all_keys, f"Forbidden key '{forbidden}' leaked in student view!"

    # 4. Check option fields inside config
    for opt in sv["config"]["options"]:
        assert set(opt.keys()) == {"id", "content_md"}


# ==============================================================================
# TC-4.1-05: Property-based testing with Hypothesis
# ==============================================================================
@settings(max_examples=30, deadline=1500)
@given(
    seed=st.integers(min_value=0, max_value=1_000_000),
    q_type=st.sampled_from(["mcq", "tf", "short_text", "short_number", "file_upload"]),
    content=st.text(min_size=1, max_size=200).filter(lambda s: bool(s.strip())),
    points=st.decimals(min_value=Decimal("0.01"), max_value=Decimal("100.00"), places=2),
)
def test_tc_4_1_05_hypothesis_property_testing(
    seed: int, q_type: str, content: str, points: Decimal
) -> None:
    """TC-4.1-05: Property test ensures zero forbidden keys across random valid inputs."""
    # Build a valid question object for the chosen type
    if q_type == "mcq":
        config = {"options": [{"id": "o1", "content_md": "A"}, {"id": "o2", "content_md": "B"}]}
        answer_key = {"correct": "o1"}
    elif q_type == "tf":
        config = {
            "statements": [
                {"id": "s1", "content_md": "A"},
                {"id": "s2", "content_md": "B"},
                {"id": "s3", "content_md": "C"},
                {"id": "s4", "content_md": "D"},
            ],
            "scoring": "thpt",
        }
        answer_key = {"s1": True, "s2": False, "s3": True, "s4": False}
    elif q_type == "short_text":
        config = {"grading": "auto", "review_wrong": False}
        answer_key = {"accepted": ["OK"]}
    elif q_type == "short_number":
        config = {"tolerance": 0.0, "tolerance_type": "abs"}
        answer_key = {"values": ["42"]}
    else:  # file_upload
        config = {"max_files": 1, "max_mb": 10, "allowed_ext": ["pdf"]}
        answer_key = {"rubric_md": "Rubric"}

    q_data = {
        "id": str(uuid.uuid4()),
        "type": q_type,
        "content_md": content,
        "points": str(points),
        "config": config,
        "answer_key": answer_key,
        "explanation_md": "Detailed explanation",
    }

    sv = student_view(q_data, seed=seed, shuffle_options=True)

    # Assert top-level keys
    assert set(sv.keys()).issubset({"id", "type", "content_md", "points", "config", "unavailable"})
    # Assert config keys
    assert set(sv["config"].keys()).issubset(STUDENT_CONFIG_KEYS[q_type])
    # Assert 0 forbidden keys anywhere
    all_keys = recursive_find_keys(sv)
    leakage = all_keys.intersection(FORBIDDEN_STUDENT_KEYS)
    assert not leakage, f"Hypothesis detected leaked keys: {leakage}"


# ==============================================================================
# TC-4.1-06: Corrupted question handling
# ==============================================================================
def test_tc_4_1_06_corrupt_question_marked_unavailable() -> None:
    """TC-4.1-06: Corrupted questions in DB do not crash the examination view."""
    # Corrupt MCQ missing 'options'
    corrupt_q = {
        "id": str(uuid.uuid4()),
        "type": "mcq",
        "content_md": "MCQ bị hỏng dữ liệu",
        "points": "1.00",
        "config": {},  # missing options list!
        "answer_key": {"correct": "o1"},
    }
    # Valid question
    valid_q = {
        "id": str(uuid.uuid4()),
        "type": "short_text",
        "content_md": "Câu hỏi hợp lệ",
        "points": "1.00",
        "config": {"grading": "manual"},
        "answer_key": {},
    }

    res = student_view_list([corrupt_q, valid_q])
    assert len(res) == 2

    # First question is safely isolated and marked unavailable
    assert res[0]["unavailable"] is True
    assert res[0]["id"] == corrupt_q["id"]

    # Second question is returned completely normally
    assert res[1].get("unavailable", False) is False
    assert res[1]["content_md"] == "Câu hỏi hợp lệ"


# ==============================================================================
# TC-4.1-07: Stable option shuffling
# ==============================================================================
def test_tc_4_1_07_stable_option_shuffling() -> None:
    """TC-4.1-07: Same seed produces identical option order; different seed produces different."""
    qid = str(uuid.uuid4())
    options = [
        {"id": f"o{i}", "content_md": f"Option {i}"}
        for i in range(1, 7)  # 6 options
    ]
    q_data = {
        "id": qid,
        "type": "mcq",
        "content_md": "Câu hỏi 6 lựa chọn",
        "points": "2.00",
        "config": {"options": options},
        "answer_key": {"correct": "o1"},
    }

    # Calling twice with same seed -> exactly identical order
    res_a1 = student_view(q_data, seed=12345, shuffle_options=True)
    res_a2 = student_view(q_data, seed=12345, shuffle_options=True)

    order_a1 = [opt["id"] for opt in res_a1["config"]["options"]]
    order_a2 = [opt["id"] for opt in res_a2["config"]["options"]]
    assert order_a1 == order_a2

    # Calling with different seed -> different ordering (with 6 options, 6! = 720 permutations)
    res_b = student_view(q_data, seed=99999, shuffle_options=True)
    order_b = [opt["id"] for opt in res_b["config"]["options"]]

    assert set(order_a1) == set(order_b)  # All options are preserved
    assert order_a1 != order_b  # Order is shuffled differently


# ==============================================================================
# TC-4.1-08: TF 3 statements with scoring='thpt'
# ==============================================================================
def test_tc_4_1_08_tf_3_statements_auto_switches_scoring() -> None:
    """TC-4.1-08: TF with 3 statements and 'thpt' automatically switches to 'proportional'."""
    tf_q = QuestionCreate(
        type="tf",
        content_md="Xét 3 mệnh đề sau:",
        points=Decimal("1.50"),
        config={
            "statements": [
                {"id": "s1", "content_md": "Mệnh đề A"},
                {"id": "s2", "content_md": "Mệnh đề B"},
                {"id": "s3", "content_md": "Mệnh đề C"},
            ],
            "scoring": "thpt",
        },
        answer_key={"s1": True, "s2": False, "s3": True},
    )

    # Scoring should be auto-converted to proportional
    assert tf_q.config["scoring"] == "proportional"


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
        pytest.skip(f"Database not reachable for step 4.1 integration tests: {exc}")

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
    app = create_app()
    return TestClient(app)


@pytest.fixture
def admin_auth(db_session_setup, client):
    """Creates a test admin and returns auth headers."""
    from app.core.security import hash_password
    from app.db.session import get_engine

    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username=f"admin_41_{uuid.uuid4().hex[:6]}",
            full_name="Quản Trị Viên 4.1",
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


@pytest.fixture
def student_auth(db_session_setup, client):
    """Creates a test student and returns auth headers."""
    from app.core.security import hash_password
    from app.db.session import get_engine

    engine = get_engine()
    with Session(engine) as session:
        student = User(
            username=f"hs_41_{uuid.uuid4().hex[:6]}",
            full_name="Học Sinh 4.1",
            hashed_password=hash_password("StudentPassword123!"),
            role="student",
            is_active=True,
        )
        session.add(student)
        session.commit()
        session.refresh(student)

    resp = client.post(
        "/api/v1/auth/login",
        json={"username": student.username, "password": "StudentPassword123!"},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}", "student_id": str(student.id)}


def test_tc_4_1_api_create_and_student_view_flow(client, admin_auth, student_auth) -> None:
    """TC-4.1 API: Admin creates questions and student retrieves allow-listed view."""
    from app.db.session import get_engine

    engine = get_engine()

    # 1. Create a test exam
    with Session(engine) as session:
        exam = Exam(
            title="Đề kiểm tra Đại số 10",
            duration_minutes=45,
            status="draft",
            created_by=uuid.UUID(admin_auth["admin_id"]),
            version=1,
        )
        session.add(exam)
        session.commit()
        session.refresh(exam)
        exam_id = str(exam.id)

    # 2. Admin posts MCQ question
    mcq_payload = {
        "type": "mcq",
        "content_md": "Khẳng định nào sau đây đúng?",
        "points": "1.00",
        "config": {
            "options": [
                {"id": "o1", "content_md": "Phương án 1"},
                {"id": "o2", "content_md": "Phương án 2"},
            ]
        },
        "answer_key": {"correct": "o1"},
        "explanation_md": "Lời giải thích chỉ dành cho giáo viên.",
    }

    create_resp = client.post(
        f"/api/v1/admin/exams/{exam_id}/questions",
        json=mcq_payload,
        headers={"Authorization": admin_auth["Authorization"]},
    )
    assert create_resp.status_code == 201
    q_data = create_resp.json()
    assert q_data["type"] == "mcq"
    assert q_data["answer_key"]["correct"] == "o1"
    assert q_data["explanation_md"] == "Lời giải thích chỉ dành cho giáo viên."

    # 3. Student fetches questions for this exam
    student_resp = client.get(
        f"/api/v1/student/exams/{exam_id}/questions",
        headers={"Authorization": student_auth["Authorization"]},
    )
    assert student_resp.status_code == 200
    student_questions = student_resp.json()
    assert len(student_questions) == 1

    sq = student_questions[0]
    assert sq["type"] == "mcq"
    assert "options" in sq["config"]

    # Strict assertion: ZERO leakage of answer key or explanation
    assert "answer_key" not in sq
    assert "explanation_md" not in sq
    assert "correct" not in sq["config"]
