"""Time helpers for the existing naive-UTC database timestamp columns."""

from datetime import datetime, timezone


def utcnow_naive() -> datetime:
    """Return current UTC as a naive datetime for legacy timezone-naive columns."""
    return datetime.now(timezone.utc).replace(tzinfo=None)
