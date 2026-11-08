"""Tests for Step 2.4: Authoritative Time Service (Clock) and Pure Deadline Functions.

Verifies:
    TC-2.4-01: Standard deadline calculation: start + duration accurate to the second
    TC-2.4-02: Hard cutoff: deadline clamped by close_at when start + duration > close_at
    TC-2.4-03: Accommodations / extra_seconds extensions; negative extra_seconds rejected
    TC-2.4-04: Grace period boundary: writable at deadline + grace, rejected at +1µs
    TC-2.4-05: Naive datetimes (without timezone) unconditionally rejected with ValueError
    TC-2.4-06: remaining_seconds boundary: 0 at deadline, 0 after deadline, 1 at 0.2s remaining
    TC-2.4-07: Clock skew detection in /readyz: logs warning when app and DB drift > 2s
    TC-2.4-08: Codebase grep check: no datetime.now() calls outside core/time.py
"""

import logging
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.time import (
    FakeClock,
    compute_deadline,
    get_clock,
    is_writable,
    remaining_seconds,
)
from app.main import create_app


def test_tc_2_4_01_standard_deadline():
    """TC-2.4-01: Standard deadline calculation: start=10:00, 30 min -> 10:30:00."""
    start = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)
    deadline = compute_deadline(
        started_at=start,
        duration_minutes=30,
        extra_seconds=0,
        close_at=None,
    )
    expected = datetime(2026, 11, 8, 10, 30, 0, tzinfo=UTC)
    assert deadline == expected


def test_tc_2_4_02_clamped_by_close_at():
    """TC-2.4-02: Clamped by close_at: start=10:00, 60 min, close_at=10:20 -> 10:20:00."""
    start = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)
    close_at = datetime(2026, 11, 8, 10, 20, 0, tzinfo=UTC)
    deadline = compute_deadline(
        started_at=start,
        duration_minutes=60,
        extra_seconds=0,
        close_at=close_at,
    )
    assert deadline == close_at


def test_tc_2_4_03_extra_seconds_extension():
    """TC-2.4-03: extra_seconds adds time; negative extra_seconds raises ValueError."""
    start = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)

    # 1. 300 extra seconds (+5 minutes)
    deadline = compute_deadline(
        started_at=start,
        duration_minutes=30,
        extra_seconds=300,
        close_at=None,
    )
    expected = datetime(2026, 11, 8, 10, 35, 0, tzinfo=UTC)
    assert deadline == expected

    # 2. Negative extra_seconds must raise ValueError
    with pytest.raises(ValueError) as exc_info:
        compute_deadline(
            started_at=start,
            duration_minutes=30,
            extra_seconds=-10,
        )
    assert "không được âm" in str(exc_info.value)


def test_tc_2_4_04_grace_period_boundaries():
    """TC-2.4-04: Writable at deadline + grace; rejected at deadline + grace + 1µs."""
    deadline = datetime(2026, 11, 8, 10, 30, 0, tzinfo=UTC)
    grace = 5  # 5 seconds grace

    # Case A: Exact boundary (deadline + 5s) -> True
    exact_boundary = deadline + timedelta(seconds=grace)
    assert is_writable(now=exact_boundary, deadline_at=deadline, grace_seconds=grace) is True

    # Case B: 1 microsecond after boundary -> False
    beyond_boundary = exact_boundary + timedelta(microseconds=1)
    assert is_writable(now=beyond_boundary, deadline_at=deadline, grace_seconds=grace) is False

    # Case C: 1 second before deadline -> True
    before_deadline = deadline - timedelta(seconds=1)
    assert is_writable(now=before_deadline, deadline_at=deadline, grace_seconds=grace) is True


def test_tc_2_4_05_naive_datetime_rejection():
    """TC-2.4-05: Naive datetimes (without timezone) are strictly rejected with ValueError."""
    naive_time = datetime(2026, 11, 8, 10, 0, 0)  # No tzinfo
    aware_time = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)

    # 1. compute_deadline rejects naive started_at
    with pytest.raises(ValueError) as exc:
        compute_deadline(started_at=naive_time, duration_minutes=30)
    assert "múi giờ" in str(exc.value)

    # 2. compute_deadline rejects naive close_at
    with pytest.raises(ValueError) as exc:
        compute_deadline(started_at=aware_time, duration_minutes=30, close_at=naive_time)
    assert "múi giờ" in str(exc.value)

    # 3. is_writable rejects naive now
    with pytest.raises(ValueError) as exc:
        is_writable(now=naive_time, deadline_at=aware_time)
    assert "múi giờ" in str(exc.value)

    # 4. remaining_seconds rejects naive deadline_at
    with pytest.raises(ValueError) as exc:
        remaining_seconds(now=aware_time, deadline_at=naive_time)
    assert "múi giờ" in str(exc.value)


def test_tc_2_4_06_remaining_seconds_boundaries():
    """TC-2.4-06: remaining_seconds is ceiling rounded, never negative, 0 after deadline."""
    deadline = datetime(2026, 11, 8, 10, 30, 0, tzinfo=UTC)

    # Case 1: Exact deadline -> 0
    assert remaining_seconds(now=deadline, deadline_at=deadline) == 0

    # Case 2: Past deadline -> 0 (never negative)
    past_time = deadline + timedelta(seconds=15)
    assert remaining_seconds(now=past_time, deadline_at=deadline) == 0

    # Case 3: 0.2 seconds remaining -> 1 (ceiling rounded up)
    almost_done = deadline - timedelta(seconds=0.2)
    assert remaining_seconds(now=almost_done, deadline_at=deadline) == 1

    # Case 4: 59.1 seconds remaining -> 60
    assert remaining_seconds(now=deadline - timedelta(seconds=59.1), deadline_at=deadline) == 60


def test_tc_2_4_07_clock_skew_monitoring():
    """TC-2.4-07: Clock skew > 2.0s triggers warning log in /readyz while returning ready."""
    import io
    from unittest.mock import MagicMock, patch

    app = create_app()

    log_capture = io.StringIO()
    handler = logging.StreamHandler(log_capture)
    target_logger = logging.getLogger("app.system")
    target_logger.addHandler(handler)
    target_logger.setLevel(logging.WARNING)

    try:
        db_time = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)
        app_time = datetime(2026, 11, 8, 10, 0, 5, tzinfo=UTC)  # 5 seconds ahead
        fake_clock = FakeClock(app_time)
        app.dependency_overrides[get_clock] = lambda: fake_clock

        # Mock DB engine connection to isolate test from network variations
        mock_conn = MagicMock()
        mock_conn.execute.return_value.first.return_value = (1, db_time)
        mock_engine = MagicMock()
        mock_engine.connect.return_value.__enter__.return_value = mock_conn

        with patch("app.routers.system.create_engine", return_value=mock_engine):
            client = TestClient(app)
            res = client.get("/readyz")

        # App remains ready / 200
        assert res.status_code == 200

        # Warning log is emitted for clock skew
        logs = log_capture.getvalue()
        assert "Cảnh báo lệch giờ" in logs
        assert "5.000s" in logs
    finally:
        target_logger.removeHandler(handler)


def test_tc_2_4_08_grep_datetime_now_forbidden():
    """TC-2.4-08: Codebase scan ensures datetime.now() is called ONLY in core/time.py."""
    backend_app_dir = Path(__file__).resolve().parent.parent / "app"

    # Run grep for datetime.now( in backend/app/
    cmd = [
        "grep",
        "-rn",
        "datetime.now(",
        str(backend_app_dir),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)

    matches = [line for line in result.stdout.strip().split("\n") if line]
    assert len(matches) == 1, f"Found unexpected datetime.now() calls: {matches}"
    # The only permitted match is in app/core/time.py
    assert "app/core/time.py" in matches[0]


def test_server_time_endpoint_with_clock_dependency():
    """Verifies /api/v1/time returns exact time controlled by FakeClock."""
    app = create_app()
    fixed_time = datetime(2026, 11, 8, 12, 34, 56, tzinfo=UTC)
    fake_clock = FakeClock(fixed_time)
    app.dependency_overrides[get_clock] = lambda: fake_clock

    client = TestClient(app)
    res = client.get("/api/v1/time")
    assert res.status_code == 200
    data = res.json()
    assert data["server_now"] == "2026-11-08T12:34:56Z"
    assert data["epoch_ms"] == int(fixed_time.timestamp() * 1000)
