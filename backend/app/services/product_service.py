"""Combine stored image recognition with the exact label text that was read."""
import re

from app.ocr.product_parser import recognize_product


def _label_section(text: str, labels: str) -> str | None:
    match = re.search(rf"(?:^|\n)\s*(?:{labels})\s*[:\-]?\s*([^\n]+)", text, re.IGNORECASE)
    return match.group(1).strip()[:800] if match else None


def identify_product(visual: dict | None, raw_text: str, user_label: str | None = None) -> dict:
    text_match = recognize_product(raw_text, user_label=user_label)
    product = dict(visual or {})
    if text_match["source"] == "package_text":
        agrees = product.get("category") == text_match["category"]
        visual_evidence = product.get("evidence", []) if agrees else []
        if product.get("category") and not agrees:
            product.setdefault("limitations", []).append(f"Label text suggests {text_match['category']}; compare this with the visual alternatives.")
        product.update(text_match)
        product["source"] = "image_and_text" if agrees else "package_text"
        product["status"] = "recognized"
        product["confidence_kind"] = "text_match_score"
        product["evidence"] = visual_evidence + text_match["evidence"]
    elif not product.get("category") and text_match["source"] == "user_label":
        product.update(text_match)
        product.update(status="user_supplied", confidence_kind="user_supplied")
    elif not product:
        product.update(text_match)
    size = re.search(r"\b\d+(?:[.,]\d+)?\s*(?:ml|cl|litres?|liters?|kg|grams?|g|oz)\b", raw_text, re.IGNORECASE)
    product["label_details"] = {
        "package_size": size.group(0) if size else None,
        "ingredients": _label_section(raw_text, "ingredients?"),
        "allergens": _label_section(raw_text, "allergens?|contains|may contain"),
        "storage_instructions": _label_section(raw_text, "storage(?: instructions)?"),
        "nutrition_text": _label_section(raw_text, "nutrition(?:al)?(?: information| facts| values)?"),
    }
    return product
