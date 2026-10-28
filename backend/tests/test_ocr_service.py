from pathlib import Path
from types import SimpleNamespace

from app.ocr import service
from app.ocr.date_parser import extract_expiry_date


def test_expiry_confidence_ignores_unrelated_low_confidence_lines():
    confidence = service._expiry_line_confidence(
        ["unrelated package noise", "EXP 11/2027"],
        [[4.0, 9.0, 12.0], [98.0, 96.0]],
        {"date_detected": True, "expiry_text": "11/2027"},
    )

    assert confidence == 0.97


def test_labelled_expiry_avoids_slow_neural_retry(monkeypatch):
    monkeypatch.setattr(service, "_tesseract_command", lambda: "tesseract")
    monkeypatch.setattr(
        service,
        "_read_tesseract",
        lambda _path, _command: ("USE BY 30 OCT 2026", 0.31),
    )

    def fail_if_called(_path):
        raise AssertionError("RapidOCR should not rerun a labelled, parseable date")

    monkeypatch.setattr(service, "_read_rapidocr", fail_if_called)
    result = service.extract_text_from_image("synthetic-package.png")

    assert result["expiry_date"] == "2026-10-30"
    assert result["expiry_label"] == "USE BY"
    assert result["provider"] == "tesseract"


def test_unlabelled_low_confidence_date_still_uses_neural_retry(monkeypatch):
    monkeypatch.setattr(service, "_tesseract_command", lambda: "tesseract")
    monkeypatch.setattr(
        service,
        "_read_tesseract",
        lambda _path, _command: ("05/2027", 0.31),
    )
    neural_calls = []

    def read_with_rapidocr(_path):
        neural_calls.append(True)
        return "BEST BEFORE 05/2027", 0.9

    monkeypatch.setattr(service, "_read_rapidocr", read_with_rapidocr)
    result = service.extract_text_from_image("synthetic-package.png")

    assert neural_calls
    assert result["expiry_date"] == "2027-05-31"
    assert result["provider"] == "rapidocr"


def test_angled_dot_matrix_package_date_is_read_from_the_photo():
    photo = Path(__file__).parent / "fixtures" / "angled_dot_matrix_date.jpg"
    text, confidence = service._read_rapidocr(str(photo))
    parsed = extract_expiry_date(text)
    assert parsed["expiry_date"].isoformat() == "2019-12-31"
    assert parsed["expiry_label"] == "unlabeled date"
    assert confidence is not None


def test_stamp_retry_keeps_manufacture_context(monkeypatch):
    outputs = iter([
        SimpleNamespace(txts=("MFG 01/01/2025",), scores=(0.95,)),
        SimpleNamespace(txts=("31/12/2026",), scores=(0.95,)),
    ])
    monkeypatch.setattr(service, "_rapid_reader", lambda _image: next(outputs))
    monkeypatch.setattr(service, "_stamp_views", lambda _path: iter(["stamp crop"]))
    text, _confidence = service._read_rapidocr("package.jpg")
    assert "MFG" in text
    assert extract_expiry_date(text)["expiry_date"] is None
