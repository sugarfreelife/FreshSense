"""REAL expiry-date extraction from OCR text via regex.

Supported (case-insensitive):
  EXP 12/09/2026, EXP: 12-09-2026, EXPIRY 12.09.2026
  BEST BEFORE 12/09/2026, BEST BEFORE: 09/2026
  BB: 09/2026, BB 09-2026
  USE BY 2026-09-12, YYYY-MM-DD, DD/MM/YYYY, DD-MM-YYYY, DD.MM.YYYY, MM/YYYY
Normalization -> datetime.date. Invalid dates (e.g. 31/02/2026) are ignored.
"""

import re
from datetime import date

_PATTERNS = [
    # labelled full dates: EXP / EXPIRY / BEST BEFORE / USE BY / BB + date
    re.compile(
        r"(?:EXP(?:IRY|IRATION)?|BEST\s*BEFORE|USE\s*BY|B?B)\s*[:\-]?\s*"
        r"(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})",
        re.IGNORECASE,
    ),
    # ISO YYYY-MM-DD / YYYY/MM/DD
    re.compile(r"\b(\d{4})[\/\-.](\d{1,2})[\/\-.](\d{1,2})\b"),
    # labelled month/year: BB: 09/2026
    re.compile(
        r"(?:EXP(?:IRY)?|BEST\s*BEFORE|USE\s*BY|B?B)\s*[:\-]?\s*(\d{1,2})[\/\-.](\d{4})",
        re.IGNORECASE,
    ),
    # bare DD/MM/YYYY
    re.compile(r"\b(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})\b"),
]


def _valid_day_month_year(day: int, month: int, year: int) -> date | None:
    if year < 100:
        year += 2000
    try:
        return date(year, month, day)
    except ValueError:
        return None


def extract_expiry_date(text: str) -> dict:
    """Return {expiry_date: date|None, date_detected: bool}."""
    if not text:
        return {"expiry_date": None, "date_detected": False}
    text = text.strip()

    m = _PATTERNS[0].search(text)
    if m:
        d = _valid_day_month_year(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            return {"expiry_date": d, "date_detected": True}

    m = _PATTERNS[1].search(text)
    if m:
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
            return {"expiry_date": d, "date_detected": True}
        except ValueError:
            pass

    m = _PATTERNS[2].search(text)
    if m:
        month, year = int(m.group(1)), int(m.group(2))
        try:
            import calendar

            last_day = calendar.monthrange(year, month)[1]
            return {"expiry_date": date(year, month, last_day), "date_detected": True}
        except (ValueError, calendar.IllegalMonthError):
            pass

    m = _PATTERNS[3].search(text)
    if m:
        d = _valid_day_month_year(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        if d:
            return {"expiry_date": d, "date_detected": True}

    return {"expiry_date": None, "date_detected": False}
