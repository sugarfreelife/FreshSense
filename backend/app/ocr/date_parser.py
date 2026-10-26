"""Parse expiry dates from OCR text without confusing them with manufacture dates."""

from datetime import date
import calendar
import re


_DATE = r"(?:\d{4}[-/.]\d{1,2}[-/.]\d{1,2}|\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}|\d{1,2}\s*[A-Za-z]{3,9}\s*\d{2,4}|[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{2,4}|\d{1,2}[-/.]\d{2,4})"
_EXPIRY_LABEL = re.compile(
    rf"\b(?:DATE\s+OF\s+)?(?:EXP(?:IR(?:Y|ATION))?|BEST\s*BEFORE(?:\s+END)?|BEST\s*BY|USE\s*BY|USE\s*BEFORE|CONSUME\s*BY|SELL\s*BY|VALID\s+(?:UNTIL|THROUGH|THRU)|BBE|BB)\s*(?:DATE|DT)?\s*[:#-]?\s*({_DATE})",
    re.IGNORECASE,
)
_MANUFACTURE_LABEL = re.compile(r"\b(?:MFG|MFD|MANUFACTURED|PROD(?:UCTION)?|PACKED|PKD)\b", re.I)


def _parse(value: str) -> date | None:
    try:
        year_first = re.fullmatch(r"(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})", value)
        if year_first:
            return date(*(int(part) for part in year_first.groups()))

        numeric = re.fullmatch(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{2,4})", value)
        if numeric:
            day, month, year = (int(part) for part in numeric.groups())
            return date(year + (2000 if year < 100 else 0), month, day)

        month_year = re.fullmatch(r"(\d{1,2})[-/.](\d{4})", value)
        if month_year:
            month, year = (int(part) for part in month_year.groups())
            return date(year, month, calendar.monthrange(year, month)[1])

        textual = re.fullmatch(r"(\d{1,2})\s*([A-Za-z]{3,9})\s*(\d{2,4})", value)
        if textual:
            day, month_name, year = textual.groups()
            month = next(index for index in range(1, 13) if calendar.month_name[index].lower().startswith(month_name.lower()))
            year = int(year)
            return date(year + (2000 if year < 100 else 0), month, int(day))

        textual = re.fullmatch(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{2,4})", value)
        if textual:
            month_name, day, year = textual.groups()
            month = next(index for index in range(1, 13) if calendar.month_name[index].lower().startswith(month_name.lower()))
            year = int(year)
            return date(year + (2000 if year < 100 else 0), month, int(day))
    except (ValueError, StopIteration, OverflowError):
        return None
    return None


def _supported_year(value: date | None) -> date | None:
    """Reject OCR noise that looks like a syntactically valid distant year."""
    if value is None or not 1900 <= value.year <= 2100:
        return None
    return value


def extract_expiry_date(text: str) -> dict:
    """Return a date only when it follows an expiry/best-before label.

    Labelled dates are preferred. If OCR found a manufacture/packing label,
    unlabeled dates are deliberately ignored so the production date is not
    presented as the expiry date.
    """
    for match in _EXPIRY_LABEL.finditer(text or ""):
        expiry = _supported_year(_parse(match.group(1)))
        if expiry:
            label = match.group(0).split(match.group(1), 1)[0].strip(" :#-\t")
            return {
                "expiry_date": expiry,
                "date_detected": True,
                "expiry_label": label or "expiry",
                "expiry_text": match.group(1).strip(),
            }

    # Some package stamps print day/month only (for example, 04JUL). Keep that
    # evidence visible, but do not manufacture a year or use it in safety rules.
    partial = re.compile(
        r"\b(?:(?P<day_first>[0-9OQ]{1,2})\s*[-/. ]?\s*(?P<month_first>[A-Z]{3,9})|(?P<month_second>[A-Z]{3,9})\s*[-/. ]?\s*(?P<day_second>[0-9OQ]{1,2}))\b",
        re.I,
    )
    partial_text = re.sub(
        r"\b[OQ](?=\d\s*[A-Z]{3,9}\b)",
        "0",
        text or "",
        flags=re.I,
    )
    for match in partial.finditer(partial_text):
        month_name = match.group("month_first") or match.group("month_second")
        if not any(calendar.month_name[index].lower().startswith(month_name.lower()) for index in range(1, 13)):
            continue
        context_start = max(0, match.start() - 45)
        context = partial_text[context_start:match.start()]
        label_match = re.search(
            r"(?:BEST(?:\s*(?:BEFORE|BY))?|USE\s*BY|USE\s*BEFORE|EXP(?:IR(?:Y|ATION))?|BBE|BB)\s*(?:DATE|DT)?\s*[:#-]?\s*$",
            context,
            re.I,
        )
        if label_match:
            label = re.sub(r"\s+", " ", label_match.group(0)).strip(" :#-\t")
            return {
                "expiry_date": None,
                "date_detected": False,
                "expiry_label": label or "expiry",
                "expiry_text": match.group(0).strip(),
            }

    if _MANUFACTURE_LABEL.search(text or ""):
        return {"expiry_date": None, "date_detected": False, "expiry_label": None, "expiry_text": None}

    # Date-only fallback is safe only when there is exactly one date candidate.
    matches = list(re.finditer(_DATE, text or "", re.I))
    if len(matches) == 1:
        expiry = _supported_year(_parse(matches[0].group(0)))
        if expiry:
            return {"expiry_date": expiry, "date_detected": True, "expiry_label": "unlabeled date", "expiry_text": matches[0].group(0)}
    return {"expiry_date": None, "date_detected": False, "expiry_label": None, "expiry_text": None}
