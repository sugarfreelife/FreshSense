from pathlib import Path

import pytest

from app.ocr.service import _tesseract_command, extract_text_from_image


SAMPLE_DIR = Path(__file__).resolve().parents[2] / "data" / "demo_scan_images"
EXPECTED_DATES = {
    "baked-beans-best-before-05-2027.png": "2027-05-31",
    "canned-tuna-exp-11-2027.png": "2027-11-30",
    "orange-juice-exp-15-jan-2027.png": "2027-01-15",
    "whole-wheat-bread-use-by-30-oct-2026.png": "2026-10-30",
}


@pytest.mark.skipif(
    _tesseract_command() is None,
    reason="Tesseract is required for image OCR samples",
)
@pytest.mark.parametrize(("image_name", "expected_date"), EXPECTED_DATES.items())
def test_demo_package_photo_expiry_dates(image_name, expected_date):
    result = extract_text_from_image(str(SAMPLE_DIR / image_name))

    assert result["date_detected"] is True
    assert result["expiry_date"] == expected_date
    assert result["expiry_label"]
