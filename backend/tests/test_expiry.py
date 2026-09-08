from datetime import date, timedelta

from app.services.expiry_service import compute_expiry


def test_expired():
    past = date.today() - timedelta(days=1)
    out = compute_expiry(past)
    assert out["status"] == "expired"
    assert out["days_remaining"] < 0 or out["days_remaining"] == -1


def test_expiring_soon():
    soon = date.today() + timedelta(days=3)
    out = compute_expiry(soon)
    assert out["status"] == "expiring_soon"
    assert out["days_remaining"] == 3


def test_valid():
    future = date.today() + timedelta(days=30)
    out = compute_expiry(future)
    assert out["status"] == "valid"
    assert out["days_remaining"] == 30


def test_unknown_none():
    out = compute_expiry(None)
    assert out["status"] == "unknown"
    assert out["days_remaining"] is None
