"""Authoritative Business Time Service & Pure Deadline Calculation Functions.

Implements:
    - Clock Protocol, SystemClock, and FakeClock (for deterministic testing).
    - Pure domain functions: compute_deadline, is_writable, remaining_seconds.
    - Strict timezone-aware validation: naive datetimes are unconditionally rejected.
"""

import math
from datetime import UTC, datetime, timedelta
from typing import Protocol


class Clock(Protocol):
    """Abstract clock interface providing authoritative UTC business timestamps."""

    def now(self) -> datetime:
        """Returns current timezone-aware UTC datetime."""
        ...


class SystemClock:
    """Production clock using real system UTC time."""

    def now(self) -> datetime:
        """Returns current system UTC datetime."""
        return datetime.now(UTC)


class FakeClock:
    """Test clock that can be frozen, set to specific timestamps, or stepped deterministically."""

    def __init__(self, initial_time: datetime | None = None) -> None:
        if initial_time is not None:
            if initial_time.tzinfo is None:
                raise ValueError("initial_time phải là datetime có múi giờ (timezone-aware).")
            self._current_time = initial_time
        else:
            self._current_time = datetime(2026, 11, 8, 10, 0, 0, tzinfo=UTC)

    def now(self) -> datetime:
        """Returns frozen or stepped test UTC datetime."""
        return self._current_time

    def set_time(self, new_time: datetime) -> None:
        """Sets the clock to an exact timezone-aware datetime."""
        if new_time.tzinfo is None:
            raise ValueError("new_time phải là datetime có múi giờ (timezone-aware).")
        self._current_time = new_time

    def advance(self, seconds: float) -> None:
        """Advances the clock by a given number of seconds."""
        self._current_time += timedelta(seconds=seconds)


# Global default clock instance
_default_clock: Clock = SystemClock()


def get_clock() -> Clock:
    """FastAPI dependency yielding the configured Clock service."""
    return _default_clock


def set_default_clock(clock: Clock) -> None:
    """Overrides the global clock instance (useful for test fixtures)."""
    global _default_clock
    _default_clock = clock


def compute_deadline(
    started_at: datetime,
    duration_minutes: int,
    extra_seconds: int = 0,
    close_at: datetime | None = None,
) -> datetime:
    """Computes authoritative attempt submission deadline.

    Formula:
        deadline = started_at + duration_minutes + extra_seconds
        If close_at is specified, deadline cannot exceed close_at.

    Args:
        started_at: When the student started the attempt (must be timezone-aware).
        duration_minutes: Standard exam duration in minutes (> 0).
        extra_seconds: Accommodations / bonus seconds granted by teacher (>= 0).
        close_at: Hard exam closure time (optional, must be timezone-aware).

    Returns:
        Authoritative deadline datetime in UTC.

    Raises:
        ValueError: If datetimes are naive or parameters are negative.
    """
    if started_at.tzinfo is None:
        raise ValueError("started_at phải là datetime có múi giờ (timezone-aware).")
    if close_at is not None and close_at.tzinfo is None:
        raise ValueError("close_at phải là datetime có múi giờ (timezone-aware).")
    if duration_minutes <= 0:
        raise ValueError("duration_minutes phải lớn hơn 0.")
    if extra_seconds < 0:
        raise ValueError("extra_seconds không được âm.")

    target_deadline = started_at + timedelta(minutes=duration_minutes, seconds=extra_seconds)

    if close_at is not None:
        return min(target_deadline, close_at)
    return target_deadline


def is_writable(now: datetime, deadline_at: datetime, grace_seconds: int = 5) -> bool:
    """Evaluates whether an attempt is still writable for auto-save and submission.

    An attempt is writable up to deadline_at + grace_seconds (to account for network jitter).
    At exact boundary (now == deadline_at + grace_seconds), returns True.
    Beyond boundary (now > deadline_at + grace_seconds), returns False.
    """
    if now.tzinfo is None:
        raise ValueError("now phải là datetime có múi giờ (timezone-aware).")
    if deadline_at.tzinfo is None:
        raise ValueError("deadline_at phải là datetime có múi giờ (timezone-aware).")
    if grace_seconds < 0:
        raise ValueError("grace_seconds không được âm.")

    boundary = deadline_at + timedelta(seconds=grace_seconds)
    return now <= boundary


def remaining_seconds(now: datetime, deadline_at: datetime) -> int:
    """Calculates remaining seconds before deadline, ceiling rounded, never negative."""
    if now.tzinfo is None:
        raise ValueError("now phải là datetime có múi giờ (timezone-aware).")
    if deadline_at.tzinfo is None:
        raise ValueError("deadline_at phải là datetime có múi giờ (timezone-aware).")

    diff_seconds = (deadline_at - now).total_seconds()
    return max(0, math.ceil(diff_seconds))
