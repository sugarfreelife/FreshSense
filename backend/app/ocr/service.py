"""OCR service: tries easyocr only if installed; never fabricates dates."""

from app.ocr.date_parser import extract_expiry_date


def extract_text_from_image(image_path: str, raw_text_override: str | None = None) -> dict:
    """Return {raw_text, expiry_date, date_detected, provider}.

    If easyocr is unavailable (default Phase 1), returns date_detected False
    with empty raw_text unless raw_text_override is supplied (used by tests
    and manual label entry). Never invents a date.
    """
    provider = "easyocr"
    raw_text = ""
    try:
        import easyocr  # type: ignore  # optional Phase-2 dependency

        reader = easyocr.Reader(["en"], gpu=False)
        results = reader.readtext(image_path)
        raw_text = " ".join(r[1] for r in results) if results else ""
    except ImportError:
        provider = "unavailable"
        raw_text = raw_text_override or ""
    except Exception:
        provider = "easyocr-error"
        raw_text = raw_text_override or ""

    if raw_text_override is not None and not raw_text:
        raw_text = raw_text_override

    parsed = extract_expiry_date(raw_text)
    return {
        "raw_text": raw_text,
        "expiry_date": parsed["expiry_date"].isoformat() if parsed["expiry_date"] else None,
        "date_detected": parsed["date_detected"],
        "provider": provider,
        "message": (
            "OCR engine not installed (Phase-2 optional dependency). "
            "No date fabricated; supply label text manually."
            if provider == "unavailable" and not parsed["date_detected"]
            else ""
        ),
    }
