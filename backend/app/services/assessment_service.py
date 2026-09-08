"""Orchestrates a full scan: vision + ocr + fusion + decision."""

from datetime import date

from app.services import decision_service, fusion_service


def assess_scan(
    vision: dict | None = None,
    sensor: dict | None = None,
    ocr: dict | None = None,
    expiry_date: date | str | None = None,
) -> dict:
    evidence = fusion_service.normalize_evidence(vision=vision, sensor=sensor, ocr=ocr)
    modalities = evidence.get("modalities_used", [])
    result = decision_service.decide(
        vision=vision,
        sensor=sensor,
        ocr=ocr,
        expiry_date=expiry_date if expiry_date is not None else (ocr or {}).get("expiry_date"),
        modalities_used=modalities,
    )
    result["evidence"] = evidence
    return result
