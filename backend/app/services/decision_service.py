"""Deterministic Phase-1 decision rules. No ML training claims."""

from datetime import date

from app.core.enums import ExpiryStatus, FreshnessEnum
from app.services.expiry_service import compute_expiry

HIGH_VOC_THRESHOLD = 700.0


def decide(
    vision: dict | None = None,
    sensor: dict | None = None,
    ocr: dict | None = None,
    expiry_date: date | str | None = None,
    modalities_used: list[str] | None = None,
) -> dict:
    warnings: list[str] = []
    modalities: list[str] = list(modalities_used) if modalities_used else []

    vision_freshness = (vision or {}).get("freshness")
    raw_vision_confidence = (vision or {}).get("confidence")
    has_vision_confidence = raw_vision_confidence is not None
    vision_conf = float(raw_vision_confidence) if has_vision_confidence else 0.0
    gas = (sensor or {}).get("gas_value")

    # Resolve expiry date: explicit param wins, else OCR payload
    exp_date = expiry_date
    if exp_date is None and ocr:
        exp_date = ocr.get("expiry_date")
    if isinstance(exp_date, str):
        try:
            exp_date = date.fromisoformat(exp_date)
        except ValueError:
            exp_date = None

    expiry = compute_expiry(exp_date)
    status = expiry["status"]

    # --- deterministic rules ---
    if vision_freshness == FreshnessEnum.SPOILED.value and gas is not None and gas >= HIGH_VOC_THRESHOLD:
        freshness = FreshnessEnum.SPOILED.value
        confidence = max(vision_conf, 0.85)
        recommendation = "CAUTION_DO_NOT_CONSUME"
        warnings.append("HIGH_CONCERN: visual spoilage indicators plus elevated VOC reading.")
    elif status == ExpiryStatus.EXPIRED.value and vision_freshness == FreshnessEnum.FRESH.value:
        freshness = FreshnessEnum.MODERATELY_FRESH.value
        confidence = 0.6
        recommendation = "CHECK_EXPIRY"
        warnings.append("EXPIRY_WARNING: product is past its expiry date despite appearing fresh.")
    elif status == ExpiryStatus.EXPIRED.value:
        freshness = FreshnessEnum.SPOILED.value
        confidence = 0.75
        recommendation = "CAUTION_DO_NOT_CONSUME"
        warnings.append("EXPIRED: product is past its expiry date.")
    elif status == ExpiryStatus.EXPIRING_SOON.value:
        freshness = vision_freshness if vision_freshness else FreshnessEnum.MODERATELY_FRESH.value
        confidence = vision_conf if has_vision_confidence else 0.55
        recommendation = "CONSUME_SOON"
        warnings.append("EXPIRING_SOON: consume within a few days.")
    elif vision_freshness == FreshnessEnum.SPOILED.value:
        freshness = FreshnessEnum.SPOILED.value
        confidence = vision_conf if has_vision_confidence else 0.7
        recommendation = "CAUTION_DO_NOT_CONSUME"
        warnings.append("SPOILAGE_INDICATED: visual cues suggest spoilage.")
    elif vision_freshness == FreshnessEnum.MODERATELY_FRESH.value:
        freshness = FreshnessEnum.MODERATELY_FRESH.value
        confidence = vision_conf if has_vision_confidence else 0.6
        recommendation = "CONSUME_SOON"
    elif vision_freshness == FreshnessEnum.FRESH.value:
        freshness = FreshnessEnum.FRESH.value
        confidence = vision_conf if has_vision_confidence else 0.7
        recommendation = "CONSUME_NOW" if gas is None or gas < HIGH_VOC_THRESHOLD else "CONSUME_SOON"
        if gas is not None and gas >= HIGH_VOC_THRESHOLD:
            warnings.append("ELEVATED_VOC: gas reading is high despite fresh appearance; consume soon.")
    else:
        # No usable evidence
        freshness = FreshnessEnum.MODERATELY_FRESH.value
        confidence = 0.4
        recommendation = "CHECK_EXPIRY"
        warnings.append("INSUFFICIENT_EVIDENCE: no reliable modality available.")

    if gas is not None and gas >= HIGH_VOC_THRESHOLD and not any("VOC" in w or "HIGH_CONCERN" in w for w in warnings):
        warnings.append("ELEVATED_VOC: volatile organic compound level is high.")

    return {
        "freshness": freshness,
        "confidence": round(float(confidence), 3),
        "recommendation": recommendation,
        "warnings": warnings,
        "modalities_used": modalities,
        "expiry_status": status,
        "days_remaining": expiry["days_remaining"],
    }
