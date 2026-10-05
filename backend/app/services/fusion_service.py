"""Normalize evidence and identify which inputs can affect the decision."""


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

    if sensor is not None and sensor.get("gas_value") is not None:
        evidence["sensor"] = {
            "gas_value": sensor.get("gas_value"),
            "temperature": sensor.get("temperature"),
            "humidity": sensor.get("humidity"),
        }
        modalities_used.append("sensor")

    if ocr is not None and ocr.get("expiry_date"):
        evidence["ocr"] = {
            "expiry_date": ocr.get("expiry_date"),
            "date_detected": True,
        }
        modalities_used.append("ocr")

    evidence["modalities_used"] = modalities_used
    return evidence
