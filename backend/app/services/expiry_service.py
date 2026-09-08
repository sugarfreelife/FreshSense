"""Expiry computation. Never fabricates dates: None input -> unknown status."""

from datetime import date

from app.core.enums import ExpiryStatus

EXPIRING_SOON_THRESHOLD_DAYS = 7


def compute_expiry(expiry_date: date | None, today: date | None = None) -> dict:
    """Return {expiry_date, days_remaining, status}."""
    today = today or date.today()
    if expiry_date is None:
        return {"expiry_date": None, "days_remaining": None, "status": ExpiryStatus.UNKNOWN.value}
    days_remaining = (expiry_date - today).days
    if days_remaining <= 0:
        status = ExpiryStatus.EXPIRED.value
    elif days_remaining <= EXPIRING_SOON_THRESHOLD_DAYS:
        status = ExpiryStatus.EXPIRING_SOON.value
    else:
        status = ExpiryStatus.VALID.value
    return {"expiry_date": expiry_date, "days_remaining": days_remaining, "status": status}
