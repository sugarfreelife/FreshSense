"""Fusion: normalize evidence from vision / sensor / ocr modalities.

Handles missing modalities honestly — only lists modalities actually present.
"""


def normalize_evidence(
    vision: dict | None = None,
    sensor: dict | None = None,
    ocr: dict | None = None,
) -> dict:
    evidence: dict = {}
    modalities_used: list[str] = []

    if vision is not None:
        evidence["vision"] = {
            "freshness": vision.get("freshness"),
            "confidence": vision.get("confidence"),
            "food_type": vision.get("food_type", "unknown"),
            "model_type": vision.get("model_type", "prototype"),
        }
        modalities_used.append("vision")

    if sensor is not None and any(
        sensor.get(k) is not None for k in ("gas_value", "temperature", "humidity")
    ):
        evidence["sensor"] = {
            "gas_value": sensor.get("gas_value"),
            "temperature": sensor.get("temperature"),
            "humidity": sensor.get("humidity"),
        }
        modalities_used.append("sensor")

    if ocr is not None and (ocr.get("date_detected") or ocr.get("raw_text")):
        evidence["ocr"] = {
            "expiry_date": ocr.get("expiry_date"),
            "date_detected": bool(ocr.get("date_detected")),
            "raw_text": ocr.get("raw_text", ""),
        }
        modalities_used.append("ocr")

    evidence["modalities_used"] = modalities_used
    return evidence
