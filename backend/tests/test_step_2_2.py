"""Tests for Step 2.2: Database Models, Constraints, Alembic Migrations, and PgBouncer Engine.

Verifies:
    TC-2.2-01: alembic upgrade head -> downgrade base -> upgrade head lifecycle
    TC-2.2-02: alembic check detects model changes vs migration state
    TC-2.2-03: attempts unique constraint blocks duplicate student attempt
    TC-2.2-04: uppercase username is rejected by check constraint
    TC-2.2-05: swapping position between two questions succeeds via DEFERRABLE constraint
    TC-2.2-06: invalid attempt status is rejected by check constraint
    TC-2.2-07: stale connection recovery via pool_pre_ping
    TC-2.2-08: EXPLAIN query uses ix_attempts_active_deadline partial index
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from alembic import command
from app.cli import seed_development_data
from app.db.session import get_direct_engine, get_engine
from app.models import Attempt, Class, Exam, Question, User


@pytest.fixture(scope="module")
def alembic_config():
    """Provides Alembic Config pointing to backend configuration."""
    backend_dir = Path(__file__).resolve().parent.parent
    ini_path = backend_dir / "alembic.ini"
    cfg = Config(str(ini_path))
    cfg.set_main_option("script_location", str(backend_dir / "alembic"))
    return cfg


@pytest.fixture(autouse=True)
def ensure_db_clean():
    """Ensures database tables exist and cleans up data between tests."""
    engine = get_engine()
    # Check if database is reachable; if not, skip postgres-specific tests
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        pytest.skip(f"Database not reachable for step 2.2 tests: {exc}")

    yield

    # Clean up test rows in reverse dependency order
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


def test_tc_2_2_01_alembic_lifecycle(alembic_config):
    """TC-2.2-01: alembic upgrade head -> downgrade base -> upgrade head lifecycle."""
    # 1. Upgrade to head
    command.upgrade(alembic_config, "head")
    engine = get_direct_engine()
    inspector = inspect(engine)
    tables_head = set(inspector.get_table_names())
    expected_tables = {
        "users",
        "sessions",
        "classes",
        "class_members",
        "exams",
        "exam_classes",
        "questions",
        "attempts",
        "answers",
        "files",
        "audit_logs",
        "alembic_version",
    }
    assert expected_tables.issubset(tables_head)

    # 2. Downgrade to base
    command.downgrade(alembic_config, "base")
    inspector = inspect(engine)
    tables_base = set(inspector.get_table_names())
    assert "users" not in tables_base
    assert "exams" not in tables_base
    assert "questions" not in tables_base

    # 3. Upgrade to head again
    command.upgrade(alembic_config, "head")
    inspector = inspect(engine)
    tables_rehead = set(inspector.get_table_names())
    assert expected_tables.issubset(tables_rehead)


def test_tc_2_2_02_alembic_check(alembic_config):
    """TC-2.2-02: alembic check confirms models match database migrations exactly."""
    # Ensure schema is at head
    command.upgrade(alembic_config, "head")
    # check() raises exception if there are unapplied or unmigrated model changes
    command.check(alembic_config)


def test_tc_2_2_03_unique_attempt_constraint():
    """TC-2.2-03: Unique constraint blocks duplicate student attempt for same exam."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="teacher_tc3",
            full_name="Teacher Three",
            hashed_password="hashed_pw_test",
            role="admin",
        )
        student = User(
            username="student_tc3",
            full_name="Student Three",
            hashed_password="hashed_pw_test",
            role="student",
        )
        session.add_all([admin, student])
        session.flush()

        exam = Exam(
            title="Exam TC3",
            subject="math",
            duration_minutes=30,
            status="published",
            created_by=admin.id,
        )
        session.add(exam)
        session.flush()

        now = datetime.now(UTC)
        attempt1 = Attempt(
            exam_id=exam.id,
            student_id=student.id,
            status="in_progress",
            started_at=now,
            deadline_at=now + timedelta(minutes=30),
            shuffle_seed=12345,
        )
        session.add(attempt1)
        exam_id = exam.id
        student_id = student.id
        session.commit()

    # Second attempt with same exam_id and student_id must violate UNIQUE constraint
    with pytest.raises(IntegrityError) as exc_info:
        with Session(engine) as session:
            attempt2 = Attempt(
                exam_id=exam_id,
                student_id=student_id,
                status="in_progress",
                started_at=now,
                deadline_at=now + timedelta(minutes=30),
                shuffle_seed=67890,
            )
            session.add(attempt2)
            session.commit()

    err_msg = str(exc_info.value).lower()
    assert "uq_attempts_exam_student" in str(exc_info.value) or "unique" in err_msg


def test_tc_2_2_04_username_lowercase_check_constraint():
    """TC-2.2-04: Uppercase username is rejected by check constraint; lowercase succeeds."""
    engine = get_engine()

    # 1. Uppercase username 'Nam01' must violate ck_users_username_lower
    with pytest.raises(IntegrityError) as exc_info:
        with Session(engine) as session:
            user_upper = User(
                username="Nam01",
                full_name="Nguyen Van Nam",
                hashed_password="hashed_pw_test",
                role="student",
            )
            session.add(user_upper)
            session.commit()

    err_msg = str(exc_info.value).lower()
    assert "ck_users_username_lower" in str(exc_info.value) or "check" in err_msg

    # 2. Lowercase username 'nam01' succeeds
    with Session(engine) as session:
        user_lower = User(
            username="nam01",
            full_name="Nguyen Van Nam",
            hashed_password="hashed_pw_test",
            role="student",
        )
        session.add(user_lower)
        session.commit()

        db_user = session.execute(
            select(User).where(User.username == "nam01")
        ).scalar_one_or_none()
        assert db_user is not None
        assert db_user.username == "nam01"


def test_tc_2_2_05_deferrable_position_swap():
    """TC-2.2-05: Swapping position between two questions succeeds via DEFERRABLE constraint."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="teacher_tc5",
            full_name="Teacher Five",
            hashed_password="hashed_pw_test",
            role="admin",
        )
        session.add(admin)
        session.flush()

        exam = Exam(
            title="Exam TC5 Deferrable",
            subject="computer_science",
            duration_minutes=45,
            status="draft",
            created_by=admin.id,
        )
        session.add(exam)
        session.flush()

        q1 = Question(
            exam_id=exam.id,
            position=1,
            question_type="mcq",
            content_md="Question One",
            config={"options": []},
            answer_key={"correct": "o1"},
            points=Decimal("1.00"),
        )
        q2 = Question(
            exam_id=exam.id,
            position=2,
            question_type="short_answer",
            content_md="Question Two",
            config={},
            answer_key={"target": 42.0},
            points=Decimal("1.00"),
        )
        session.add_all([q1, q2])
        session.commit()

        q1_id, q2_id = q1.id, q2.id

    # In a single transaction, swap positions directly
    with Session(engine) as session:
        obj1 = session.get(Question, q1_id)
        obj2 = session.get(Question, q2_id)
        assert obj1 is not None and obj2 is not None

        # Without DEFERRABLE, obj1.position = 2 would fail immediately because obj2 has position 2.
        # With DEFERRABLE INITIALLY DEFERRED, constraint check is deferred to commit time.
        obj1.position = 2
        obj2.position = 1
        session.commit()

    # Verify positions after commit
    with Session(engine) as session:
        obj1 = session.get(Question, q1_id)
        obj2 = session.get(Question, q2_id)
        assert obj1.position == 2
        assert obj2.position == 1


def test_tc_2_2_06_invalid_status_check_constraint():
    """TC-2.2-06: Invalid attempt status 'foo' is rejected by check constraint."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="teacher_tc6",
            full_name="Teacher Six",
            hashed_password="hashed_pw_test",
            role="admin",
        )
        student = User(
            username="student_tc6",
            full_name="Student Six",
            hashed_password="hashed_pw_test",
            role="student",
        )
        session.add_all([admin, student])
        session.flush()

        exam = Exam(
            title="Exam TC6 Status Check",
            subject="math",
            duration_minutes=30,
            status="published",
            created_by=admin.id,
        )
        session.add(exam)
        session.flush()

        now = datetime.now(UTC)
        attempt_invalid = Attempt(
            exam_id=exam.id,
            student_id=student.id,
            status="foo",  # Invalid status
            started_at=now,
            deadline_at=now + timedelta(minutes=30),
            shuffle_seed=99999,
        )
        session.add(attempt_invalid)
        with pytest.raises(IntegrityError) as exc_info:
            session.commit()

    assert "ck_attempts_status" in str(exc_info.value) or "check" in str(exc_info.value).lower()


def test_tc_2_2_07_pool_pre_ping_recovery():
    """TC-2.2-07: Automatic reconnection recovery via pool_pre_ping."""
    engine = get_engine()

    # 1. Establish initial connection and invalidate it to simulate severed socket
    with engine.connect() as conn:
        conn.invalidate()

    # 2. Next query automatically recovers transparently via pool_pre_ping=True
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


def test_tc_2_2_08_sweeper_partial_index():
    """TC-2.2-08: EXPLAIN verifies ix_attempts_active_deadline partial index."""
    engine = get_engine()
    with engine.connect() as conn:
        # Check index existence in PostgreSQL catalogs
        check_idx = conn.execute(
            text(
                "SELECT indexname, indexdef FROM pg_indexes "
                "WHERE tablename = 'attempts' AND indexname = 'ix_attempts_active_deadline';"
            )
        ).mappings().first()

        assert check_idx is not None
        assert "deadline_at" in check_idx["indexdef"]
        assert "status" in check_idx["indexdef"] and "in_progress" in check_idx["indexdef"]

        # Turn off sequential scan to verify planner uses the partial index
        conn.execute(text("SET LOCAL enable_seqscan = off;"))
        explain_result = conn.execute(
            text(
                "EXPLAIN (FORMAT TEXT) SELECT id FROM attempts "
                "WHERE status = 'in_progress' AND deadline_at < now();"
            )
        ).fetchall()

        plan_text = "\n".join(row[0] for row in explain_result)
        assert "ix_attempts_active_deadline" in plan_text


def test_cli_seed_development_data():
    """Verifies development seed CLI command populates classes and exam with 4 question formats."""
    engine = get_engine()
    with Session(engine) as session:
        admin = User(
            username="admin_seed_test",
            full_name="Admin Seeder",
            hashed_password="hashed_pw_test",
            role="admin",
        )
        session.add(admin)
        session.commit()

    # Run seed function
    seed_development_data(admin_username="admin_seed_test")

    # Verify classes and exam were created
    with Session(engine) as session:
        classes = session.execute(
            select(Class).where(Class.code.in_(["TOAN-10A1", "TIN-10A2"]))
        ).scalars().all()
        assert len(classes) == 2

        exam = session.execute(
            select(Exam).where(Exam.title.like("%Đề kiểm tra khảo sát%"))
        ).scalar_one_or_none()
        assert exam is not None
        assert exam.duration_minutes == 45

        # Check that all 4 question types are present
        questions = session.execute(
            select(Question).where(Question.exam_id == exam.id).order_by(Question.position.asc())
        ).scalars().all()
        assert len(questions) == 4

        qtypes = [q.question_type for q in questions]
        assert qtypes == ["mcq", "true_false", "short_answer", "file_upload"]

        # Check true_false format and step_threshold scoring
        tf_q = questions[1]
        assert tf_q.config["format"] == "group_4"
        assert tf_q.config["scoring_mode"] == "step_threshold"
        assert len(tf_q.config["items"]) == 4
        assert "thresholds" in tf_q.answer_key
