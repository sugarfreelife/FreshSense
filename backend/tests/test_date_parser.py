from datetime import date

from app.ocr.date_parser import extract_expiry_date


def test_exp_slash():
    out = extract_expiry_date("EXP 12/09/2026")
    assert out["date_detected"] is True
    assert out["expiry_date"] == date(2026, 9, 12)


def test_exp_dash_colon():
    out = extract_expiry_date("EXP: 12-09-2026")
    assert out["date_detected"] is True
    assert out["expiry_date"] == date(2026, 9, 12)


def test_best_before():
    out = extract_expiry_date("BEST BEFORE 01/02/2027")
    assert out["date_detected"] is True
    assert out["expiry_date"] == date(2027, 2, 1)


def test_bb_month_year():
    out = extract_expiry_date("BB: 09/2026")
    assert out["date_detected"] is True
    assert out["expiry_date"].year == 2026 and out["expiry_date"].month == 9


def test_iso():
    out = extract_expiry_date("USE BY 2026-09-12")
    assert out["date_detected"] is True
    assert out["expiry_date"] == date(2026, 9, 12)


def test_no_date_never_fabricates():
    out = extract_expiry_date("Fresh apples, tasty!")
    assert out["date_detected"] is False
    assert out["expiry_date"] is None
