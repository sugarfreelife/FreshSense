"""Read printed food-package text and parse dates without guessing."""

from pathlib import Path
import re
import shutil
from threading import Lock

from app.ocr.date_parser import extract_expiry_date

_rapid_reader = None
_rapid_reader_lock = Lock()
_EXPIRY_LABEL_LINE = re.compile(
    r"\b(?:exp(?:iry|iration)?|best\s*(?:before|by)|use\s*(?:by|before)|sell\s*by|"
    r"valid\s*(?:until|through|thru)|bbe|bb)\b",
    re.I,
)


def _expiry_line_confidence(lines: list[str], line_scores: list[list[float]], parsed: dict) -> float | None:
    """Score the recognized date and nearby label instead of unrelated package text."""
    all_scores = [score for scores in line_scores for score in scores if score >= 0]
    if not all_scores:
        return None
    if not parsed.get("date_detected"):
        return sum(all_scores) / len(all_scores) / 100

    expiry_text = parsed.get("expiry_text")
    normalized_target = re.sub(r"[^a-z0-9]", "", str(expiry_text or "").lower())
    date_lines = [
        index
        for index, line in enumerate(lines)
        if normalized_target
        and normalized_target in re.sub(r"[^a-z0-9]", "", line.lower())
    ]
    relevant_lines: set[int] = set()
    labelled_date_lines: set[int] = set()
    for index in date_lines:
        relevant_lines.add(index)
        if _EXPIRY_LABEL_LINE.search(lines[index]):
            labelled_date_lines.add(index)
        if index > 0 and _EXPIRY_LABEL_LINE.search(lines[index - 1]):
            labelled_date_lines.update((index - 1, index))
        if index + 1 < len(lines) and _EXPIRY_LABEL_LINE.search(lines[index + 1]):
            labelled_date_lines.update((index, index + 1))

    if labelled_date_lines:
        relevant_lines = labelled_date_lines
    selected_scores = [
        score
        for index in sorted(relevant_lines)
        for score in line_scores[index]
        if score >= 0
    ]
    scores = selected_scores or all_scores
    return sum(scores) / len(scores) / 100


def _tesseract_command() -> str | None:
    found = shutil.which("tesseract")
    if found:
        return found
    for candidate in (
        Path(r"C:\Program Files\Tesseract-OCR\tesseract.exe"),
        Path(r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe"),
    ):
        if candidate.is_file():
            return str(candidate)
    return None


def _read_tesseract(image_path: str, command: str) -> tuple[str, float | None]:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageOps

    pytesseract.pytesseract.tesseract_cmd = command
    with Image.open(image_path) as source:
        gray = ImageOps.grayscale(source)
        gray.thumbnail((1800, 1800))
        quick = ImageOps.autocontrast(gray)

        def read_candidate(image, page_mode: int) -> tuple[str, float | None]:
            data = pytesseract.image_to_data(
                image,
                lang="eng",
                config=f"--oem 3 --psm {page_mode}",
                output_type=pytesseract.Output.DICT,
            )
            lines: dict[tuple[str, str, str], list[str]] = {}
            line_scores: dict[tuple[str, str, str], list[float]] = {}
            for index, raw_word in enumerate(data["text"]):
                word = str(raw_word).strip()
                if not word:
                    continue
                key = (data["block_num"][index], data["par_num"][index], data["line_num"][index])
                lines.setdefault(key, []).append(word)
                score = float(data["conf"][index])
                if score >= 0:
                    line_scores.setdefault(key, []).append(score)
            line_keys = list(lines)
            line_texts = [" ".join(lines[key]) for key in line_keys]
            text = "\n".join(line_texts).strip()
            parsed = extract_expiry_date(text)
            confidence = _expiry_line_confidence(
                line_texts,
                [line_scores.get(key, []) for key in line_keys],
                parsed,
            )
            return text, confidence

        quick_text, quick_confidence = read_candidate(quick, 6)
        quick_parse = extract_expiry_date(quick_text)
        # A date read next to an explicit package instruction (EXP, USE BY,
        # BEST BEFORE, etc.) is stronger evidence than the image-wide average
        # confidence. Large photos often contain lots of irrelevant text that
        # pulls that average down. Avoid four costly full-image retries when
        # the labelled date is already parseable.
        if quick_parse["date_detected"] and quick_parse.get("expiry_label") != "unlabeled date":
            return quick_text, quick_confidence
        # Most clear package labels are solved in one OCR pass. Keep the heavier
        # multi-view retry for small, angled, or low-contrast stamps.
        if quick_parse["date_detected"] and (quick_confidence or 0) >= 0.72 and len(quick_text) >= 18:
            return quick_text, quick_confidence

        # Package dates commonly sit in a label around the middle of the
        # product. A focused crop gives Tesseract a useful scale/layout before
        # falling back to several expensive full-frame enhancement passes.
        width, height = gray.size
        focused = gray.crop(
            (int(width * 0.22), int(height * 0.20), int(width * 0.78), int(height * 0.82))
        )
        scale = min(2.0, 1600 / max(focused.size))
        if scale > 1:
            focused = focused.resize(
                (max(1, int(focused.width * scale)), max(1, int(focused.height * scale)))
            )
        for page_mode in (6, 11):
            focused_text, focused_confidence = read_candidate(focused, page_mode)
            focused_parse = extract_expiry_date(focused_text)
            if focused_parse["date_detected"] and focused_parse.get("expiry_label") != "unlabeled date":
                focused.close()
                return focused_text, focused_confidence
        focused.close()

        enlarged = gray.resize((gray.width * 2, gray.height * 2))
        variants = (
            ImageEnhance.Sharpness(ImageEnhance.Contrast(enlarged).enhance(1.8)).enhance(2.0),
            ImageOps.autocontrast(enlarged).point(lambda pixel: 255 if pixel > 165 else 0),
        )

        candidates: list[tuple[tuple[int, int, float], str, float | None]] = [
            ((int(quick_parse["date_detected"]), len(quick_text), quick_confidence or 0), quick_text, quick_confidence)
        ]
        for image in variants:
            for page_mode in (6, 11):
                text, confidence = read_candidate(image, page_mode)
                parsed = extract_expiry_date(text)
                candidates.append(((int(parsed["date_detected"]), len(text), confidence or 0), text, confidence))

    _, text, confidence = max(candidates, key=lambda candidate: candidate[0])
    return text, confidence


def _stamp_views(image_path: str):
    """Straighten dark ink and connect dot-matrix strokes for a bounded retry."""
    import numpy as np
    from PIL import Image, ImageFilter, ImageOps

    with Image.open(image_path) as source:
        gray = ImageOps.grayscale(source)
        gray.thumbnail((900, 900))
    width, height = gray.size
    stamp = gray.crop((int(width * .12), int(height * .15), int(width * .88), int(height * .85)))
    ink = stamp.point(lambda pixel: 0 if pixel < 70 else 255)
    angles = []
    for angle in range(-45, 46, 3):
        rotated = ink.rotate(angle, expand=True, fillcolor=255)
        rows = (np.asarray(rotated) < 128).sum(axis=1)
        # Horizontal text concentrates ink into rows once the stamp is level.
        score = float((rows ** 2).sum() / max(int(rows.sum()), 1))
        angles.append((score, angle))
    best_score, angle = max(angles)
    if best_score == 0:
        return
    level_score = next(score for score, candidate in angles if candidate == 0)
    if best_score < level_score * 1.15:
        angle = 0
    for threshold in (95, 70):
        mask = stamp.point(lambda pixel: 0 if pixel < threshold else 255)
        joined = mask.filter(ImageFilter.MinFilter(3))
        view = joined.rotate(angle, expand=True, fillcolor=255)
        yield view.resize((view.width * 2, view.height * 2))


def _read_rapidocr(image_path: str) -> tuple[str, float | None]:
    global _rapid_reader
    from rapidocr import RapidOCR

    if _rapid_reader is None:
        with _rapid_reader_lock:
            if _rapid_reader is None:
                # Models ship in the package; scans do not need model downloads.
                _rapid_reader = RapidOCR(params={
                    "EngineConfig.onnxruntime.intra_op_num_threads": 2,
                    "EngineConfig.onnxruntime.inter_op_num_threads": 1,
                    "Global.log_level": "error",
                })

    def read(image):
        output = _rapid_reader(image)
        lines = list(output.txts or [])
        scores = [[float(score) * 100] for score in (output.scores or [])]
        return lines, scores

    lines, scores = read(image_path)
    text = "\n".join(lines)
    parsed = extract_expiry_date(text)
    candidates = [(text, _expiry_line_confidence(lines, scores, parsed))]
    if parsed["date_detected"]:
        return candidates[0]
    for view in _stamp_views(image_path):
        stamp_lines, stamp_scores = read(view)
        # Preserve full-frame manufacture labels and other date evidence so a
        # date-only crop cannot silently turn a production date into expiry.
        combined_lines = lines + stamp_lines
        combined_scores = scores + stamp_scores
        combined = "\n".join(combined_lines)
        parsed = extract_expiry_date(combined)
        candidate = (combined, _expiry_line_confidence(combined_lines, combined_scores, parsed))
        candidates.append(candidate)
        if parsed["date_detected"]:
            return candidate
    return max(candidates, key=lambda candidate: _candidate_score(*candidate))


def _candidate_score(text: str, confidence: float | None) -> tuple[int, int, float]:
    parsed = extract_expiry_date(text)
    has_expiry_label = bool(
        re.search(r"\b(?:exp|expiry|expiration|best\s*before|use\s*by|sell\s*by)\b", text, re.I)
    )
    useful_chars = sum(character.isalnum() for character in text)
    score = int(parsed["date_detected"]) * 100 + int(bool(parsed.get("expiry_text"))) * 60 + int(has_expiry_label) * 30
    return score, useful_chars, confidence or 0


def extract_text_from_image(image_path: str, raw_text_override: str | None = None) -> dict:
    """Return recognized text, expiry date, confidence and the OCR engine used."""
    candidates: list[tuple[str, float | None, str]] = []
    errors: list[str] = []
    command = _tesseract_command()
    if command:
        try:
            raw_text, confidence = _read_tesseract(image_path, command)
            candidates.append((raw_text, confidence, "tesseract"))
        except Exception:
            errors.append("Tesseract could not process the image.")

    # Try neural OCR when Tesseract misses the expiry label or reports weak text.
    tesseract_text, tesseract_confidence = next(
        ((text, confidence) for text, confidence, provider in candidates if provider == "tesseract"),
        ("", None),
    )
    tesseract_parsed = extract_expiry_date(tesseract_text)
    has_labelled_date = (
        tesseract_parsed["date_detected"]
        and tesseract_parsed.get("expiry_label") != "unlabeled date"
    )
    if not command or not tesseract_parsed["date_detected"] or (
        (tesseract_confidence or 0) < 0.55 and not has_labelled_date
    ):
        try:
            raw_text, confidence = _read_rapidocr(image_path)
            candidates.append((raw_text, confidence, "rapidocr"))
        except ImportError:
            if not command:
                errors.append("Install Tesseract OCR or the RapidOCR package.")
        except Exception:
            errors.append("RapidOCR could not process the image.")

    if candidates:
        raw_text, confidence, provider = max(
            candidates,
            key=lambda candidate: _candidate_score(candidate[0], candidate[1]),
        )
        message = ""
    else:
        raw_text, confidence = "", None
        provider = "unavailable" if not command and any("Install " in error for error in errors) else "tesseract_error"
        message = " ".join(errors) or "The OCR engine could not read this image. Try a closer, brighter photo of the printed date."

    if raw_text_override is not None and not raw_text.strip():
        raw_text = raw_text_override.strip()
        provider = "manual"
        confidence = None

    parsed = extract_expiry_date(raw_text)
    return {
        "raw_text": raw_text,
        "expiry_date": parsed["expiry_date"].isoformat() if parsed["expiry_date"] else None,
        "date_detected": parsed["date_detected"],
        "expiry_label": parsed.get("expiry_label"),
        "expiry_text": parsed.get("expiry_text"),
        "provider": provider,
        "confidence": round(confidence, 3) if confidence is not None else None,
        "message": message if not parsed["date_detected"] else "",
    }
