from datetime import UTC, datetime


def utcnow() -> datetime:
    """
    Return current timezone-aware datetime in UTC.

    This function is the SOLE AUTHORIZED SOURCE of current time across the entire
    MATHRIX codebase to guarantee testability and eliminate timezone discrepancies.
    Scattered `datetime.now()` calls without timezone are strictly prohibited.
    """
    return datetime.now(UTC)
