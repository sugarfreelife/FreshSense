from app.ocr import service


def test_labelled_expiry_avoids_slow_neural_retry(monkeypatch):
    monkeypatch.setattr(service, "_tesseract_command", lambda: "tesseract")
    monkeypatch.setattr(
        service,
        "_read_tesseract",
        lambda _path, _command: ("USE BY 30 OCT 2026", 0.31),
    )

    def fail_if_called(_path):
        raise AssertionError("EasyOCR should not rerun a labelled, parseable date")

    monkeypatch.setattr(service, "_read_easyocr", fail_if_called)
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

    def read_with_easyocr(_path):
        neural_calls.append(True)
        return "BEST BEFORE 05/2027", 0.9

    monkeypatch.setattr(service, "_read_easyocr", read_with_easyocr)
    result = service.extract_text_from_image("synthetic-package.png")

    assert neural_calls
    assert result["expiry_date"] == "2027-05-31"
    assert result["provider"] == "easyocr"
